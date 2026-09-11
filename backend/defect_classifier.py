from pathlib import Path


DATASET_PATH = Path("dataset/mvtec_ad/bottle/test")


DEFECT_TYPES = {
    "good": "No Defect",
    "broken_large": "Broken Large",
    "broken_small": "Broken Small",
    "contamination": "Contamination"
}


def classify_defect(image_name):
    """
    Prototype defect classification.

    The MVTec Bottle dataset stores test images
    inside folders representing their defect category.
    """

    image_path = Path(image_name)

    category = image_path.parent.name

    if category in DEFECT_TYPES:
        return {
            "defect_type": DEFECT_TYPES[category],
            "category": category
        }

    return {
        "defect_type": "Unknown",
        "category": "unknown"
    }


if __name__ == "__main__":

    print("=" * 55)
    print("VisionInspect AI - Defect Classification")
    print("=" * 55)

    print("\nSupported defect types:")

    for category, name in DEFECT_TYPES.items():
        print(f"  {category} -> {name}")

    print("\nDefect classification module ready.")

    print("=" * 55)