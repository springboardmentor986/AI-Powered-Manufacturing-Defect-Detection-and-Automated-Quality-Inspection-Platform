import cv2
import json
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing.preprocess import preprocess_image


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "saved_models"
OUTPUT_DIR = BASE_DIR / "diagnostics" / "results"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLD_FILE = BASE_DIR / "inference" / "thresholds.json"

CATEGORIES = [
    "bottle",
    "cable",
    "capsule",
    "carpet",
    "grid",
    "hazelnut",
    "leather",
    "metal_nut",
    "pill",
    "screw",
    "tile",
    "toothbrush",
    "transistor",
    "wood",
    "zipper"
]

IMAGE_SIZE = (224, 224)


# ============================================================
# AUTOENCODER
# EXACT SAME ARCHITECTURE AS TRAINING
# ============================================================

class ConvAutoencoder(nn.Module):

    def __init__(self):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),

            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.Conv2d(128, 256, 3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU()
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(
                256, 128, 3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.ConvTranspose2d(
                128, 64, 3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.ConvTranspose2d(
                64, 32, 3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.BatchNorm2d(32),
            nn.ReLU(),

            nn.ConvTranspose2d(
                32, 3, 3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.Sigmoid()
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


# ============================================================
# LOAD THRESHOLDS
# ============================================================

with open(THRESHOLD_FILE, "r") as f:
    thresholds = json.load(f)


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("DEVICE:", device)


# ============================================================
# LOAD MODEL
# ============================================================

def load_model(category):

    model_path = MODEL_DIR / f"{category}_autoencoder.pth"

    model = ConvAutoencoder().to(device)

    state = torch.load(
        model_path,
        map_location=device
    )

    model.load_state_dict(state)
    model.eval()

    return model


# ============================================================
# PROCESS ONE IMAGE
# ============================================================

def diagnose_image(category, image_path, model):

    original = cv2.imread(str(image_path))

    if original is None:
        return

    # --------------------------------------------------------
    # SAME PREPROCESSING USED FOR AE
    # --------------------------------------------------------

    processed, _ = preprocess_image(image_path)

    tensor = torch.from_numpy(
        np.transpose(processed, (2, 0, 1))
    ).unsqueeze(0).float().to(device)

    # --------------------------------------------------------
    # RECONSTRUCTION
    # --------------------------------------------------------

    with torch.no_grad():
        reconstruction = model(tensor)

    reconstruction = reconstruction.squeeze(0)
    reconstruction = reconstruction.cpu().numpy()
    reconstruction = np.transpose(
        reconstruction,
        (1, 2, 0)
    )

    # --------------------------------------------------------
    # ANOMALY MAP
    # --------------------------------------------------------

    input_img = processed

    diff = np.abs(
        input_img - reconstruction
    )

    anomaly_map = np.mean(diff, axis=2)

    # Normalize anomaly map for visualization

    anomaly_visual = cv2.normalize(
        anomaly_map,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    ).astype(np.uint8)

    # Smooth anomaly map

    anomaly_visual = cv2.GaussianBlur(
        anomaly_visual,
        (5, 5),
        0
    )

    # --------------------------------------------------------
    # THRESHOLD ANOMALY MAP
    # --------------------------------------------------------

    threshold = thresholds[category]["threshold"]

    binary = (
        anomaly_map > threshold
    ).astype(np.uint8) * 255

    # Remove tiny noise

    kernel = np.ones((5, 5), np.uint8)

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        kernel
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel
    )

    # --------------------------------------------------------
    # FIND CONNECTED COMPONENTS
    # --------------------------------------------------------

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary
    )

    boxes = []

    for i in range(1, num_labels):

        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]

        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]

        area = stats[i, cv2.CC_STAT_AREA]

        # Ignore extremely tiny regions

        if area < 20:
            continue

        boxes.append({
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h),
            "area": int(area)
        })

    # --------------------------------------------------------
    # DRAW BOXES
    # --------------------------------------------------------

    display = cv2.resize(
        original,
        IMAGE_SIZE
    )

    for box in boxes:

        x = box["x"]
        y = box["y"]
        w = box["w"]
        h = box["h"]

        cv2.rectangle(
            display,
            (x, y),
            (x + w, y + h),
            (0, 0, 255),
            2
        )

    # --------------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------------

    category_dir = OUTPUT_DIR / category
    category_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    stem = image_path.stem

    cv2.imwrite(
        str(category_dir / f"{stem}_original.png"),
        display
    )

    cv2.imwrite(
        str(category_dir / f"{stem}_anomaly.png"),
        anomaly_visual
    )

    cv2.imwrite(
        str(category_dir / f"{stem}_mask.png"),
        binary
    )

    cv2.imwrite(
        str(category_dir / f"{stem}_boxed.png"),
        display
    )

    print(
        f"{category:12s} | "
        f"{image_path.name:12s} | "
        f"AE threshold={threshold:.8f} | "
        f"boxes={len(boxes)}"
    )


# ============================================================
# RUN ALL 15 CATEGORIES
# ============================================================

print("\n==========================================")
print("VISIONINSPECT AI - AE DIAGNOSTICS")
print("==========================================\n")

for category in CATEGORIES:

    print(f"\n--- {category.upper()} ---")

    model = load_model(category)

    test_dir = DATASET_DIR / category / "test"

    defect_folders = [
        p for p in test_dir.iterdir()
        if p.is_dir() and p.name != "good"
    ]

    # Take one image from EACH defect type

    for defect_folder in defect_folders:

        images = sorted(
            list(defect_folder.glob("*.png")) +
            list(defect_folder.glob("*.jpg")) +
            list(defect_folder.glob("*.jpeg"))
        )

        if not images:
            continue

        image_path = images[0]

        diagnose_image(
            category,
            image_path,
            model
        )

print("\n==========================================")
print("DIAGNOSTIC COMPLETE")
print("==========================================")
print(f"\nResults saved to:")
print(OUTPUT_DIR)