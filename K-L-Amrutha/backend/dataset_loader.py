from pathlib import Path

DATASET_PATH = Path(__file__).resolve().parent / "data" / "mvtec_ad"

def load_mvtec_dataset():
    """Scans the MVTec AD directory and indexes available dataset categories and image paths."""
    if not DATASET_PATH.exists():
        return {"error": f"Dataset directory '{DATASET_PATH}' not found."}

    dataset_summary = {}

    # Iterate through product category folders (e.g., bottle, grid)
    for category_path in sorted(DATASET_PATH.iterdir()):
        category = category_path.name

        if category_path.is_dir():
            dataset_summary[category] = {"test_samples": 0, "categories": []}
            test_path = category_path / "test"

            if test_path.exists():
                # Count sample defect images within categories
                for defect_folder in sorted(test_path.iterdir()):
                    defect_type = defect_folder.name
                    if defect_folder.is_dir():
                        images = [path for path in defect_folder.iterdir() if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.bmp'}]
                        dataset_summary[category]["test_samples"] += len(images)
                        dataset_summary[category]["categories"].append(defect_type)

    return dataset_summary