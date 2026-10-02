import os
import cv2
import torch
import torch.nn as nn
import numpy as np


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "saved_models")

IMAGE_SIZE = (224, 224)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

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
    "zipper",
]


# ============================================================
# AUTOENCODER
# ============================================================

class ConvAutoencoder(nn.Module):

    def __init__(self):

        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, 2, 1),
            nn.ReLU(),

            nn.Conv2d(32, 64, 3, 2, 1),
            nn.ReLU(),

            nn.Conv2d(64, 128, 3, 2, 1),
            nn.ReLU(),

            nn.Conv2d(128, 256, 3, 2, 1),
            nn.ReLU(),
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(
                256, 128, 3, 2, 1, 1
            ),
            nn.ReLU(),

            nn.ConvTranspose2d(
                128, 64, 3, 2, 1, 1
            ),
            nn.ReLU(),

            nn.ConvTranspose2d(
                64, 32, 3, 2, 1, 1
            ),
            nn.ReLU(),

            nn.ConvTranspose2d(
                32, 3, 3, 2, 1, 1
            ),
            nn.Sigmoid(),
        )

    def forward(self, x):

        return self.decoder(
            self.encoder(x)
        )


# ============================================================
# LOAD MODEL
# ============================================================

def load_model(category):

    model_path = os.path.join(
        MODEL_DIR,
        f"{category}_autoencoder.pth"
    )

    model = ConvAutoencoder().to(DEVICE)

    checkpoint = torch.load(
        model_path,
        map_location=DEVICE,
        weights_only=False
    )

    if isinstance(checkpoint, dict):

        if "model_state_dict" in checkpoint:

            model.load_state_dict(
                checkpoint["model_state_dict"]
            )

        elif "state_dict" in checkpoint:

            model.load_state_dict(
                checkpoint["state_dict"]
            )

        else:

            model.load_state_dict(checkpoint)

    else:

        model.load_state_dict(checkpoint)

    model.eval()

    return model


# ============================================================
# RECONSTRUCTION ERROR
# ============================================================

def get_error(model, image_path):

    image = cv2.imread(image_path)

    if image is None:
        return None

    image = cv2.resize(
        image,
        IMAGE_SIZE
    )

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    image = image.astype(
        np.float32
    ) / 255.0

    image = np.transpose(
        image,
        (2, 0, 1)
    )

    image = np.expand_dims(
        image,
        axis=0
    )

    tensor = torch.tensor(
        image,
        dtype=torch.float32
    ).to(DEVICE)

    with torch.no_grad():

        reconstructed = model(tensor)

        error = torch.mean(
            (tensor - reconstructed) ** 2
        ).item()

    return error


# ============================================================
# COLLECT FOLDER
# ============================================================

def collect_folder(model, folder):

    errors = []

    if not os.path.exists(folder):
        return errors

    files = sorted([
        f for f in os.listdir(folder)
        if f.lower().endswith(
            (".png", ".jpg", ".jpeg", ".bmp")
        )
    ])

    for filename in files:

        path = os.path.join(
            folder,
            filename
        )

        error = get_error(
            model,
            path
        )

        if error is not None:
            errors.append(error)

    return np.array(
        errors,
        dtype=np.float32
    )


# ============================================================
# STATISTICS
# ============================================================

def stats(errors):

    if len(errors) == 0:

        return {
            "count": 0,
            "min": 0,
            "max": 0,
            "mean": 0,
            "median": 0,
        }

    return {
        "count": len(errors),
        "min": float(np.min(errors)),
        "max": float(np.max(errors)),
        "mean": float(np.mean(errors)),
        "median": float(np.median(errors)),
    }


# ============================================================
# ANALYZE CATEGORY
# ============================================================

def analyze_category(category):

    print()
    print("=" * 75)
    print(f"{category.upper()}")
    print("=" * 75)

    model = load_model(category)

    # --------------------------------------------------------
    # TRAIN GOOD
    # --------------------------------------------------------

    train_good_dir = os.path.join(
        DATASET_DIR,
        category,
        "train",
        "good"
    )

    train_good = collect_folder(
        model,
        train_good_dir
    )

    # --------------------------------------------------------
    # TEST GOOD
    # --------------------------------------------------------

    test_good_dir = os.path.join(
        DATASET_DIR,
        category,
        "test",
        "good"
    )

    test_good = collect_folder(
        model,
        test_good_dir
    )

    # --------------------------------------------------------
    # TEST DEFECTS
    # --------------------------------------------------------

    test_dir = os.path.join(
        DATASET_DIR,
        category,
        "test"
    )

    all_defects = []

    if os.path.exists(test_dir):

        for folder in sorted(
            os.listdir(test_dir)
        ):

            if folder == "good":
                continue

            folder_path = os.path.join(
                test_dir,
                folder
            )

            if not os.path.isdir(folder_path):
                continue

            errors = collect_folder(
                model,
                folder_path
            )

            all_defects.extend(
                errors.tolist()
            )

    all_defects = np.array(
        all_defects,
        dtype=np.float32
    )

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    train_stats = stats(train_good)
    good_stats = stats(test_good)
    defect_stats = stats(all_defects)

    print()
    print(
        f"TRAIN GOOD : "
        f"{train_stats['count']} images"
    )

    print(
        f"  Min    : {train_stats['min']:.8f}"
    )

    print(
        f"  Max    : {train_stats['max']:.8f}"
    )

    print(
        f"  Mean   : {train_stats['mean']:.8f}"
    )

    print(
        f"  Median : {train_stats['median']:.8f}"
    )

    print()
    print(
        f"TEST GOOD : "
        f"{good_stats['count']} images"
    )

    print(
        f"  Min    : {good_stats['min']:.8f}"
    )

    print(
        f"  Max    : {good_stats['max']:.8f}"
    )

    print(
        f"  Mean   : {good_stats['mean']:.8f}"
    )

    print(
        f"  Median : {good_stats['median']:.8f}"
    )

    print()
    print(
        f"TEST DEFECT : "
        f"{defect_stats['count']} images"
    )

    print(
        f"  Min    : {defect_stats['min']:.8f}"
    )

    print(
        f"  Max    : {defect_stats['max']:.8f}"
    )

    print(
        f"  Mean   : {defect_stats['mean']:.8f}"
    )

    print(
        f"  Median : {defect_stats['median']:.8f}"
    )

    # --------------------------------------------------------
    # OVERLAP
    # --------------------------------------------------------

    if len(test_good) > 0 and len(all_defects) > 0:

        good_max = np.max(test_good)
        defect_min = np.min(all_defects)

        if good_max < defect_min:

            separation = "CLEAR"

        else:

            separation = "OVERLAP"

        print()
        print(
            f"Separation : {separation}"
        )

        print(
            f"Test GOOD max   : {good_max:.8f}"
        )

        print(
            f"Defect min      : {defect_min:.8f}"
        )

    # --------------------------------------------------------
    # GAP
    # --------------------------------------------------------

    if len(test_good) > 0 and len(all_defects) > 0:

        good_mean = np.mean(test_good)
        defect_mean = np.mean(all_defects)

        difference = (
            defect_mean - good_mean
        )

        print(
            f"Mean difference : "
            f"{difference:.8f}"
        )

    return {
        "train_good": train_stats,
        "test_good": good_stats,
        "test_defect": defect_stats,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("VISIONINSPECT AI")
    print("ALL-CATEGORY AUTOENCODER SCORE ANALYSIS")
    print("=" * 75)

    print(
        f"Device     : {DEVICE}"
    )

    print(
        f"Image size : {IMAGE_SIZE}"
    )

    results = {}

    for category in CATEGORIES:

        try:

            results[category] = analyze_category(
                category
            )

        except Exception as e:

            print()
            print(
                f"ERROR - {category}: {e}"
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 110)
    print("ALL-CATEGORY SUMMARY")
    print("=" * 110)

    print(
        f"{'Category':<15}"
        f"{'Good Mean':<14}"
        f"{'Good Max':<14}"
        f"{'Defect Mean':<14}"
        f"{'Defect Min':<14}"
        f"{'Separation':<12}"
    )

    print("-" * 110)

    for category in CATEGORIES:

        if category not in results:
            continue

        data = results[category]

        good = data["test_good"]
        defect = data["test_defect"]

        if (
            good["count"] > 0
            and defect["count"] > 0
        ):

            if good["max"] < defect["min"]:
                separation = "CLEAR"
            else:
                separation = "OVERLAP"

        else:

            separation = "N/A"

        print(
            f"{category:<15}"
            f"{good['mean']:<14.8f}"
            f"{good['max']:<14.8f}"
            f"{defect['mean']:<14.8f}"
            f"{defect['min']:<14.8f}"
            f"{separation:<12}"
        )

    print("=" * 110)

    print()
    print("Analysis completed.")


if __name__ == "__main__":

    main()