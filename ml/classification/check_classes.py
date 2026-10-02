from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"

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

print("=" * 70)
print("VISIONINSPECT AI")
print("DEFECT CLASSIFICATION - DATASET CHECK")
print("=" * 70)

for category in CATEGORIES:

    test_dir = DATASET_DIR / category / "test"

    defect_classes = []

    if test_dir.exists():

        for folder in sorted(test_dir.iterdir()):

            if folder.is_dir() and folder.name != "good":

                images = list(folder.glob("*.png"))

                if images:
                    defect_classes.append(
                        (folder.name, len(images))
                    )

    print()
    print(f"{category.upper()}")
    print("-" * 50)

    if defect_classes:

        for class_name, count in defect_classes:
            print(f"{class_name:<25} {count} images")

    else:
        print("No defect classes found.")


print()
print("=" * 70)
print("DATASET CHECK COMPLETED")
print("=" * 70)
