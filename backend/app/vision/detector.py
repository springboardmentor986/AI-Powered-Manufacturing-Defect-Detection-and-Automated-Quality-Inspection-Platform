"""
Defect detection engine for VisionInspect AI (Milestone 2 & 3).

Approach: classical anomaly detection, not deep learning. For each product
category we build a "reference profile" from the MVTec AD 'good' training
images: a pixel-wise mean and std-dev image. A new image is preprocessed
the same way and compared against the reference using patch-based
deviation scoring — the image is split into a grid of small patches, and
the WORST (highest-deviation) patch determines the anomaly signal. This
is far more sensitive to small, localized defects than a whole-image
average.

predict() returns the three vision-derived sub-scores used by the
project's severity formula (Milestone 3): size, location, and confidence.
The fourth sub-score (defect type severity) is computed by the caller
(app/routers/inspections.py) once the defect's type label is known.
"""

import math
from pathlib import Path

import numpy as np

from .preprocessing import preprocess_path

ARTIFACTS_DIR = Path("model_artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)

# Confidence score (0-100) at/above which a unit is flagged defective
DEFECT_THRESHOLD = 25

PATCH_SIZE = 8


def _reference_path(category_name: str) -> Path:
    return ARTIFACTS_DIR / f"{category_name}_reference.npz"


def build_reference(category_name: str, good_image_paths: list[str]) -> dict:
    """
    Computes and saves the mean + std reference image for a category from
    a list of 'good' (non-defective) training image paths.
    """
    stack = np.stack([preprocess_path(p) for p in good_image_paths])
    mean_img = stack.mean(axis=0)
    std_img = stack.std(axis=0) + 1e-6  # avoid divide-by-zero later

    np.savez(_reference_path(category_name), mean=mean_img, std=std_img)

    return {
        "category": category_name,
        "images_used": len(good_image_paths),
    }


def has_reference(category_name: str) -> bool:
    return _reference_path(category_name).exists()


def _patch_grid_scores(deviation: np.ndarray, patch_size: int = PATCH_SIZE):
    """
    Splits the deviation map into a grid of patches and returns:
    - a 2D array of per-patch mean deviation scores
    - the (row, col) grid index of the worst patch
    """
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
    """
    Scores a single image against its category's reference profile.

    Returns confidence_score (how anomalous the worst region is),
    size_score (how much of the image is affected), and location_score
    (how close the affected region is to the image center — a proxy for
    'functional vs cosmetic area', per the project's severity framework).
    """
    ref_path = _reference_path(category_name)
    if not ref_path.exists():
        raise FileNotFoundError(
            f"No reference profile for category '{category_name}'. "
            f"Run build_references.py first."
        )

    data = np.load(ref_path)
    mean_img, std_img = data["mean"], data["std"]

    # cap std so naturally 'busy' regions (textures, patterns) don't
    # drown out real defects after z-score normalization
    std_img = np.clip(std_img, 1e-6, 0.25)

    test_img = preprocess_path(image_path)
    deviation = np.abs(test_img - mean_img) / std_img

    grid, (worst_r, worst_c) = _patch_grid_scores(deviation, PATCH_SIZE)
    worst_score = float(grid[worst_r, worst_c])

    # --- Confidence score: how strongly the worst patch stands out ---
    confidence_score = float(min(100, round(worst_score * 5, 2)))
    is_defective = confidence_score >= DEFECT_THRESHOLD

    # --- Size score: what fraction of the image is similarly affected ---
    # patches scoring at least half the worst patch's deviation are
    # treated as "part of the same defect region"
    affected = grid >= (worst_score * 0.5)
    size_fraction = float(affected.sum()) / grid.size
    size_score = float(min(100, round(size_fraction * 400, 2)))

    # --- Location score: distance of the worst patch from image center ---
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
