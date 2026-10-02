import cv2
import shutil
import random
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset"
OUTPUT_DIR = BASE_DIR / "yolo" / "all_categories"

# ============================================================
# SETTINGS
# ============================================================

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

MIN_CONTOUR_AREA = 5
RANDOM_SEED = 42

random.seed(RANDOM_SEED)

# ============================================================
# CLEAN OLD DATASET
# ============================================================

if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)

# ============================================================
# PROCESS ALL CATEGORIES
# ============================================================

grand_images = 0
grand_boxes = 0

print("=" * 70)
print("PREPARING VERIFIED YOLO DATASETS - ALL 15 CATEGORIES")
print("=" * 70)

for category in CATEGORIES:

    print("\n" + "=" * 70)
    print(f"CATEGORY: {category}")
    print("=" * 70)

    category_dataset = DATASET_DIR / category
    category_output = OUTPUT_DIR / category

    # --------------------------------------------------------
    # Find all defect folders
    # --------------------------------------------------------

    test_dir = category_dataset / "test"
    ground_truth_dir = category_dataset / "ground_truth"

    defect_types = [
        d.name
        for d in test_dir.iterdir()
        if d.is_dir() and d.name != "good"
    ]

    print("Defect types:", ", ".join(defect_types))

    # --------------------------------------------------------
    # Temporary collected samples
    # --------------------------------------------------------

    samples = []

    for defect_type in sorted(defect_types):

        image_dir = test_dir / defect_type
        mask_dir = ground_truth_dir / defect_type

        for image_path in sorted(image_dir.glob("*.png")):

            mask_path = mask_dir / f"{image_path.stem}_mask.png"

            if not mask_path.exists():
                print(
                    f"WARNING: mask missing: "
                    f"{category}/{defect_type}/{image_path.name}"
                )
                continue

            image = cv2.imread(str(image_path))

            if image is None:
                continue

            mask = cv2.imread(
                str(mask_path),
                cv2.IMREAD_GRAYSCALE
            )

            if mask is None:
                continue

            image_height, image_width = image.shape[:2]

            # Make mask dimensions match image
            if mask.shape[:2] != (image_height, image_width):
                mask = cv2.resize(
                    mask,
                    (image_width, image_height),
                    interpolation=cv2.INTER_NEAREST
                )

            # ------------------------------------------------
            # Binary defect mask
            # ------------------------------------------------

            binary_mask = cv2.threshold(
                mask,
                127,
                255,
                cv2.THRESH_BINARY
            )[1]

            # ------------------------------------------------
            # Find connected defect regions
            # ------------------------------------------------

            contours, _ = cv2.findContours(
                binary_mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            boxes = []

            for contour in contours:

                area = cv2.contourArea(contour)

                if area < MIN_CONTOUR_AREA:
                    continue

                x, y, w, h = cv2.boundingRect(contour)

                x1 = max(0, x)
                y1 = max(0, y)
                x2 = min(image_width, x + w)
                y2 = min(image_height, y + h)

                box_width = x2 - x1
                box_height = y2 - y1

                if box_width <= 0 or box_height <= 0:
                    continue

                center_x = ((x1 + x2) / 2) / image_width
                center_y = ((y1 + y2) / 2) / image_height

                normalized_width = box_width / image_width
                normalized_height = box_height / image_height

                boxes.append(
                    f"0 {center_x:.6f} {center_y:.6f} "
                    f"{normalized_width:.6f} {normalized_height:.6f}"
                )

            if boxes:
                samples.append(
                    {
                        "image": image_path,
                        "boxes": boxes,
                        "defect_type": defect_type
                    }
                )

    # --------------------------------------------------------
    # Shuffle
    # --------------------------------------------------------

    random.shuffle(samples)

    total = len(samples)

    train_end = int(total * 0.70)
    val_end = int(total * 0.85)

    splits = {
        "train": samples[:train_end],
        "val": samples[train_end:val_end],
        "test": samples[val_end:]
    }

    # --------------------------------------------------------
    # Create directories
    # --------------------------------------------------------

    for split in ["train", "val", "test"]:

        (category_output / "images" / split).mkdir(
            parents=True,
            exist_ok=True
        )

        (category_output / "labels" / split).mkdir(
            parents=True,
            exist_ok=True
        )

    visual_dir = category_output / "ground_truth_visual"
    visual_dir.mkdir(parents=True, exist_ok=True)

    category_boxes = 0

    # --------------------------------------------------------
    # Save samples
    # --------------------------------------------------------

    for split, split_samples in splits.items():

        for sample in split_samples:

            image_path = sample["image"]
            boxes = sample["boxes"]
            defect_type = sample["defect_type"]

            unique_name = (
                f"{defect_type}_{image_path.stem}.png"
            )

            output_image = (
                category_output
                / "images"
                / split
                / unique_name
            )

            output_label = (
                category_output
                / "labels"
                / split
                / f"{defect_type}_{image_path.stem}.txt"
            )

            shutil.copy2(
                image_path,
                output_image
            )

            with open(output_label, "w") as f:
                f.write("\n".join(boxes))

            category_boxes += len(boxes)

            # ------------------------------------------------
            # Ground-truth visualization
            # ------------------------------------------------

            image = cv2.imread(str(image_path))

            h, w = image.shape[:2]

            for line in boxes:

                parts = line.split()

                cx = float(parts[1]) * w
                cy = float(parts[2]) * h
                bw = float(parts[3]) * w
                bh = float(parts[4]) * h

                x1 = int(cx - bw / 2)
                y1 = int(cy - bh / 2)
                x2 = int(cx + bw / 2)
                y2 = int(cy + bh / 2)

                cv2.rectangle(
                    image,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    2
                )

                cv2.putText(
                    image,
                    defect_type,
                    (x1, max(20, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )

            cv2.imwrite(
                str(
                    visual_dir
                    / unique_name
                ),
                image
            )

    # --------------------------------------------------------
    # data.yaml
    # --------------------------------------------------------

    yaml_path = category_output / "data.yaml"

    yaml_content = f"""path: {category_output.as_posix()}
train: images/train
val: images/val
test: images/test

names:
  0: defect
"""

    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    print(f"Images : {total}")
    print(f"Train  : {len(splits['train'])}")
    print(f"Val    : {len(splits['val'])}")
    print(f"Test   : {len(splits['test'])}")
    print(f"Boxes  : {category_boxes}")

    grand_images += total
    grand_boxes += category_boxes

# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("ALL 15 YOLO DATASETS PREPARED")
print("=" * 70)

print(f"Total images : {grand_images}")
print(f"Total boxes  : {grand_boxes}")

print(f"\nOutput:")
print(OUTPUT_DIR)

print("\nEach category contains:")
print("  images/train")
print("  images/val")
print("  images/test")
print("  labels/train")
print("  labels/val")
print("  labels/test")
print("  ground_truth_visual")
print("  data.yaml")

print("=" * 70)