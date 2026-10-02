from pathlib import Path

BASE = Path("all_categories")

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

print("=" * 80)
print("YOLO DATASET SUMMARY")
print("=" * 80)

for category in CATEGORIES:

    folder = BASE / category

    train_images = list((folder / "images" / "train").glob("*"))
    val_images = list((folder / "images" / "val").glob("*"))
    test_images = list((folder / "images" / "test").glob("*"))

    train_labels = list((folder / "labels" / "train").glob("*.txt"))
    val_labels = list((folder / "labels" / "val").glob("*.txt"))
    test_labels = list((folder / "labels" / "test").glob("*.txt"))

    train_boxes = sum(
        len(p.read_text().splitlines())
        for p in train_labels
    )

    val_boxes = sum(
        len(p.read_text().splitlines())
        for p in val_labels
    )

    test_boxes = sum(
        len(p.read_text().splitlines())
        for p in test_labels
    )

    print(
        f"{category:15} "
        f"train={len(train_images):3} "
        f"val={len(val_images):3} "
        f"test={len(test_images):3} "
        f"train_boxes={train_boxes:4} "
        f"val_boxes={val_boxes:4} "
        f"test_boxes={test_boxes:4}"
    )

print("=" * 80)