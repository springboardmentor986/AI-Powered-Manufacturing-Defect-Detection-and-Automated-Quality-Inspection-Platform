import cv2
import shutil
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset" / "bottle"
OUTPUT_DIR = BASE_DIR / "yolo" / "dataset"

IMAGES_DIR = OUTPUT_DIR / "images"
LABELS_DIR = OUTPUT_DIR / "labels"
VISUAL_DIR = OUTPUT_DIR / "ground_truth_visual"

# ============================================================
# CLEAN OLD DATASET
# ============================================================

if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
LABELS_DIR.mkdir(parents=True, exist_ok=True)
VISUAL_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# DEFECT TYPES
# ============================================================

DEFECT_TYPES = [
    "broken_large",
    "broken_small",
    "contamination"
]

# ============================================================
# SETTINGS
# ============================================================

MIN_CONTOUR_AREA = 5

total_images = 0
total_boxes = 0

print("=" * 60)
print("Preparing VERIFIED YOLO dataset")
print("=" * 60)

# ============================================================
# PROCESS EACH DEFECT TYPE
# ============================================================

for defect_type in DEFECT_TYPES:

    image_dir = DATASET_DIR / "test" / defect_type
    mask_dir = DATASET_DIR / "ground_truth" / defect_type

    print(f"\nProcessing: {defect_type}")

    image_files = sorted(image_dir.glob("*.png"))

    defect_images = 0
    defect_boxes = 0

    for image_path in image_files:

        mask_path = mask_dir / f"{image_path.stem}_mask.png"

        if not mask_path.exists():
            print(f"WARNING: Mask not found: {mask_path}")
            continue

        # ----------------------------------------------------
        # READ ORIGINAL IMAGE
        # ----------------------------------------------------

        image = cv2.imread(str(image_path))

        if image is None:
            print(f"WARNING: Could not read image: {image_path}")
            continue

        image_height, image_width = image.shape[:2]

        # ----------------------------------------------------
        # READ MASK
        # ----------------------------------------------------

        mask = cv2.imread(
            str(mask_path),
            cv2.IMREAD_GRAYSCALE
        )

        if mask is None:
            print(f"WARNING: Could not read mask: {mask_path}")
            continue

        # Make absolutely sure mask matches image dimensions
        if mask.shape[:2] != (image_height, image_width):
            mask = cv2.resize(
                mask,
                (image_width, image_height),
                interpolation=cv2.INTER_NEAREST
            )

        # ----------------------------------------------------
        # BINARY DEFECT MASK
        # ----------------------------------------------------

        binary_mask = cv2.threshold(
            mask,
            127,
            255,
            cv2.THRESH_BINARY
        )[1]

        # ----------------------------------------------------
        # REMOVE VERY SMALL NOISE
        # ----------------------------------------------------

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (3, 3)
        )

        binary_mask = cv2.morphologyEx(
            binary_mask,
            cv2.MORPH_OPEN,
            kernel
        )

        # ----------------------------------------------------
        # FIND ALL DEFECT REGIONS
        # ----------------------------------------------------

        contours, _ = cv2.findContours(
            binary_mask,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE
        )

        boxes = []

        for contour in contours:

            area = cv2.contourArea(contour)

            if area < MIN_CONTOUR_AREA:
                continue

            x, y, w, h = cv2.boundingRect(contour)

            # Clamp coordinates
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(image_width, x + w)
            y2 = min(image_height, y + h)

            w_box = x2 - x1
            h_box = y2 - y1

            if w_box <= 0 or h_box <= 0:
                continue

            # ------------------------------------------------
            # YOLO NORMALIZED FORMAT
            # ------------------------------------------------

            center_x = ((x1 + x2) / 2) / image_width
            center_y = ((y1 + y2) / 2) / image_height

            box_width = w_box / image_width
            box_height = h_box / image_height

            boxes.append(
                f"0 {center_x:.6f} {center_y:.6f} "
                f"{box_width:.6f} {box_height:.6f}"
            )

        if not boxes:
            continue

        # ----------------------------------------------------
        # UNIQUE NAME
        # ----------------------------------------------------

        unique_name = f"{defect_type}_{image_path.stem}"

        output_image = IMAGES_DIR / f"{unique_name}.png"
        output_label = LABELS_DIR / f"{unique_name}.txt"
        visual_image = VISUAL_DIR / f"{unique_name}.png"

        # ----------------------------------------------------
        # COPY IMAGE
        # ----------------------------------------------------

        shutil.copy2(
            image_path,
            output_image
        )

        # ----------------------------------------------------
        # WRITE YOLO LABEL
        # ----------------------------------------------------

        with open(output_label, "w") as f:
            f.write("\n".join(boxes))

        # ----------------------------------------------------
        # CREATE GROUND-TRUTH VISUALIZATION
        # ----------------------------------------------------

        visual = image.copy()

        for line in boxes:

            parts = line.split()

            cx = float(parts[1]) * image_width
            cy = float(parts[2]) * image_height
            bw = float(parts[3]) * image_width
            bh = float(parts[4]) * image_height

            x1 = int(cx - bw / 2)
            y1 = int(cy - bh / 2)
            x2 = int(cx + bw / 2)
            y2 = int(cy + bh / 2)

            cv2.rectangle(
                visual,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),
                2
            )

            cv2.putText(
                visual,
                defect_type,
                (x1, max(20, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )

        cv2.imwrite(
            str(visual_image),
            visual
        )

        defect_images += 1
        defect_boxes += len(boxes)

    print(f"Images       : {defect_images}")
    print(f"Bounding boxes: {defect_boxes}")

    total_images += defect_images
    total_boxes += defect_boxes

# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 60)
print("YOLO DATASET PREPARATION COMPLETED")
print("=" * 60)

print(f"Images prepared : {total_images}")
print(f"Bounding boxes  : {total_boxes}")

print(f"\nImages folder:")
print(IMAGES_DIR)

print(f"\nLabels folder:")
print(LABELS_DIR)

print(f"\nGROUND-TRUTH VISUALIZATIONS:")
print(VISUAL_DIR)

print("=" * 60)