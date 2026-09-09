from pathlib import Path


class MVTecLoader:
    def __init__(self, dataset_root):
        self.dataset_root = Path(dataset_root)

    def get_categories(self):
        return sorted(
            folder.name
            for folder in self.dataset_root.iterdir()
            if folder.is_dir()
        )

    def load_category(self, category):
        category_path = self.dataset_root / category

        if not category_path.exists():
            raise ValueError(f"Category not found: {category}")

        records = []

        # Training images
        train_path = category_path / "train"

        for defect_dir in train_path.iterdir():
            if not defect_dir.is_dir():
                continue

            for image_path in sorted(defect_dir.glob("*.png")):
                records.append({
                    "category": category,
                    "split": "train",
                    "defect_type": defect_dir.name,
                    "image_path": str(image_path),
                    "mask_path": None,
                })

        # Test images
        test_path = category_path / "test"
        ground_truth_path = category_path / "ground_truth"

        for defect_dir in test_path.iterdir():
            if not defect_dir.is_dir():
                continue

            for image_path in defect_dir.glob("*.png"):

                mask_path = None

                if defect_dir.name != "good":
                    possible_mask = (
                        ground_truth_path
                        / defect_dir.name
                        / f"{image_path.stem}_mask.png"
                    )

                    if possible_mask.exists():
                        mask_path = str(possible_mask)

                records.append({
                    "category": category,
                    "split": "test",
                    "defect_type": defect_dir.name,
                    "image_path": str(image_path),
                    "mask_path": mask_path,
                })

        return records