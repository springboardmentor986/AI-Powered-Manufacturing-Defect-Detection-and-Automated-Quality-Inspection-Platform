"""
Defect detection engine for VisionInspect AI (Milestone 2-4).

Two detection paths, chosen automatically per category:

1. Trained autoencoder (Milestone 4 upgrade) — if
   model_artifacts/<category>_autoencoder.pt exists (from
   train_autoencoder.py), the image is compared against its own
   reconstruction from a neural network trained only on normal images.
   Poorly-reconstructed regions indicate a defect.

2. Statistical baseline (Milestone 2) — if no trained model exists yet
   for a category, falls back to the original mean/std reference-profile
   z-score method.

Either way, the resulting per-pixel deviation map is scored the same
way: split into a patch grid, and the worst patch determines the
confidence/size/location scores used by the severity formula
(app/routers/inspections.py).
"""

import math
from pathlib import Path

import numpy as np

from .preprocessing import preprocess_path

ARTIFACTS_DIR = Path("model_artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)

DEFECT_THRESHOLD = 10  # confidence score (0-100) at/above which a unit is flagged defective
PATCH_SIZE = 8

# Scaling factors differ because the two methods produce deviation values
# on very different numeric scales (z-scores vs. squared reconstruction
# error). Tune these against evaluate_accuracy.py results.
STAT_SCALE = 5
AUTOENCODER_SCALE = 400

_model_cache = {}


# ---------------------------------------------------------------------
# Statistical baseline (Milestone 2)
# ---------------------------------------------------------------------

def _reference_path(category_name: str) -> Path:
    return ARTIFACTS_DIR / f"{category_name}_reference.npz"


def build_reference(category_name: str, good_image_paths: list[str]) -> dict:
    stack = np.stack([preprocess_path(p) for p in good_image_paths])
    mean_img = stack.mean(axis=0)
    std_img = stack.std(axis=0) + 1e-6
    np.savez(_reference_path(category_name), mean=mean_img, std=std_img)
    return {"category": category_name, "images_used": len(good_image_paths)}


def has_reference(category_name: str) -> bool:
    return _reference_path(category_name).exists()


def _statistical_deviation(image_path: str, category_name: str) -> np.ndarray:
    data = np.load(_reference_path(category_name))
    mean_img, std_img = data["mean"], data["std"]
    std_img = np.clip(std_img, 1e-6, 0.25)
    test_img = preprocess_path(image_path)
    return np.abs(test_img - mean_img) / std_img


# ---------------------------------------------------------------------
# Trained autoencoder (Milestone 4)
# ---------------------------------------------------------------------

def _autoencoder_path(category_name: str) -> Path:
    return ARTIFACTS_DIR / f"{category_name}_autoencoder.pt"


def has_trained_model(category_name: str) -> bool:
    return _autoencoder_path(category_name).exists()


def _load_model(category_name: str):
    if category_name in _model_cache:
        return _model_cache[category_name]

    import torch
    from .autoencoder import ConvAutoencoder

    model = ConvAutoencoder()
    model.load_state_dict(
        torch.load(_autoencoder_path(category_name), map_location="cpu")
    )
    model.eval()
    _model_cache[category_name] = model
    return model


def _autoencoder_deviation(image_path: str, category_name: str) -> np.ndarray:
    import torch

    model = _load_model(category_name)
    img = preprocess_path(image_path)  # 128x128, float32 in [0, 1]
    tensor = torch.from_numpy(img).unsqueeze(0).unsqueeze(0)  # (1, 1, 128, 128)

    with torch.no_grad():
        reconstruction = model(tensor)

    error = (tensor - reconstruction).pow(2).squeeze().numpy()
    return error


# ---------------------------------------------------------------------
# Shared patch scoring + prediction
# ---------------------------------------------------------------------

def has_reference_or_model(category_name: str) -> bool:
    return has_trained_model(category_name) or has_reference(category_name)


def _patch_grid_scores(deviation: np.ndarray, patch_size: int = PATCH_SIZE):
    h, w = deviation.shape
    rows = math.ceil(h / patch_size)
    cols = math.ceil(w / patch_size)
    grid = np.zeros((rows, cols), dtype=np.float32)

    for r in range(rows):
        for c in range(cols):
            y0, x0 = r * patch_size, c * patch_size
            patch = deviation[y0 : y0 + patch_size, x0 : x0 + patch_size]
            if patch.size > 0:
                grid[r, c] = float(patch.mean())

    worst_idx = np.unravel_index(np.argmax(grid), grid.shape)
    return grid, worst_idx


def predict(image_path: str, category_name: str) -> dict:
    if has_trained_model(category_name):
        deviation = _autoencoder_deviation(image_path, category_name)
        scale = AUTOENCODER_SCALE
    elif has_reference(category_name):
        deviation = _statistical_deviation(image_path, category_name)
        scale = STAT_SCALE
    else:
        raise FileNotFoundError(
            f"No trained model or reference profile for category "
            f"'{category_name}'. Run build_references.py or "
            f"train_autoencoder.py first."
        )

    grid, (worst_r, worst_c) = _patch_grid_scores(deviation, PATCH_SIZE)
    worst_score = float(grid[worst_r, worst_c])

    confidence_score = float(min(100, round(worst_score * scale, 2)))
    is_defective = confidence_score >= DEFECT_THRESHOLD

    affected = grid >= (worst_score * 0.5)
    size_fraction = float(affected.sum()) / grid.size
    size_score = float(min(100, round(size_fraction * 400, 2)))

    rows, cols = grid.shape
    center_r, center_c = (rows - 1) / 2, (cols - 1) / 2
    max_dist = math.sqrt(center_r**2 + center_c**2) or 1.0
    dist = math.sqrt((worst_r - center_r) ** 2 + (worst_c - center_c) ** 2)
    location_score = float(round((1 - dist / max_dist) * 100, 2))

    return {
        "result": "defective" if is_defective else "normal",
        "confidence_score": confidence_score,
        "size_score": size_score,
        "location_score": location_score,
        "patch_location": {"row": int(worst_r), "col": int(worst_c)},
    }
