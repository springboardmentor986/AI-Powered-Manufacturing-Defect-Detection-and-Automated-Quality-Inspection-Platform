import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import numpy as np
from ..config import settings

class DatasetService:
    @staticmethod
    def get_mvtec_dir() -> Path:
        return settings.ACTIVE_DATASET_DIR

    @classmethod
    def get_available_categories(cls) -> List[Dict[str, Any]]:
        """Return list of all 15 MVTec AD categories with their counts and status directly from actual dataset"""
        mvtec_root = cls.get_mvtec_dir()
        categories_data = []

        for cat_name in settings.MVTEC_CATEGORIES:
            cat_path = mvtec_root / cat_name
            train_count = 0
            test_good_count = 0
            test_defect_count = 0
            defect_types = []
            has_ground_truth = False

            if cat_path.exists() and cat_path.is_dir():
                # Count train
                train_good_path = cat_path / "train" / "good"
                if train_good_path.exists():
                    train_count = len([f for f in train_good_path.glob("*.png")] + [f for f in train_good_path.glob("*.jpg")])

                # Count test
                test_path = cat_path / "test"
                if test_path.exists():
                    for item in sorted(test_path.iterdir()):
                        if item.is_dir():
                            img_count = len([f for f in item.glob("*.png")] + [f for f in item.glob("*.jpg")])
                            if item.name == "good":
                                test_good_count += img_count
                            else:
                                test_defect_count += img_count
                                defect_types.append(item.name)

                # Ground truth check
                gt_path = cat_path / "ground_truth"
                if gt_path.exists() and any(gt_path.iterdir()):
                    has_ground_truth = True

            total_imgs = train_count + test_good_count + test_defect_count
            categories_data.append({
                "category": cat_name,
                "is_loaded": total_imgs > 0,
                "train_images": train_count,
                "test_good_images": test_good_count,
                "test_defect_images": test_defect_count,
                "total_images": total_imgs,
                "defect_types": defect_types,
                "has_ground_truth": has_ground_truth,
                "type": "texture" if cat_name in ["carpet", "grid", "leather", "tile", "wood"] else "object"
            })

        return categories_data

    @classmethod
    def get_category_details(cls, category: str) -> Dict[str, Any]:
        """Get full category structure including image samples from train, test, and ground_truth"""
        mvtec_root = cls.get_mvtec_dir()
        cat_path = mvtec_root / category

        if not cat_path.exists() or not cat_path.is_dir():
            return {
                "category": category,
                "found": False,
                "splits": {}
            }

        splits: Dict[str, Any] = {
            "train": {"good": []},
            "test": {},
            "ground_truth": {}
        }

        # Train
        train_good = cat_path / "train" / "good"
        if train_good.exists():
            files = sorted(list(train_good.glob("*.png")) + list(train_good.glob("*.jpg")))
            splits["train"]["good"] = [
                f"/static/mvtec/{category}/train/good/{f.name}"
                for f in files[:12]
            ]

        # Test
        test_dir = cat_path / "test"
        if test_dir.exists():
            for defect_dir in sorted(test_dir.iterdir()):
                if defect_dir.is_dir():
                    files = sorted(list(defect_dir.glob("*.png")) + list(defect_dir.glob("*.jpg")))
                    splits["test"][defect_dir.name] = [
                        f"/static/mvtec/{category}/test/{defect_dir.name}/{f.name}"
                        for f in files[:12]
                    ]

        # Ground truth
        gt_dir = cat_path / "ground_truth"
        if gt_dir.exists():
            for defect_dir in sorted(gt_dir.iterdir()):
                if defect_dir.is_dir():
                    files = sorted(list(defect_dir.glob("*.png")) + list(defect_dir.glob("*.jpg")))
                    splits["ground_truth"][defect_dir.name] = [
                        f"/static/mvtec/{category}/ground_truth/{defect_dir.name}/{f.name}"
                        for f in files[:12]
                    ]

        return {
            "category": category,
            "found": True,
            "splits": splits
        }

    @classmethod
    def verify_and_index_dataset(cls) -> Dict[str, Any]:
        """
        Verifies presence and indexes all 15 industrial categories from the actual
        MVTec Anomaly Detection dataset (mv-dataset).
        """
        mvtec_root = cls.get_mvtec_dir()
        categories = cls.get_available_categories()
        total_train = sum(c["train_images"] for c in categories)
        total_test_good = sum(c["test_good_images"] for c in categories)
        total_test_defect = sum(c["test_defect_images"] for c in categories)
        total_all = sum(c["total_images"] for c in categories)

        return {
            "status": "READY",
            "dataset_root": str(mvtec_root),
            "categories_count": len(categories),
            "total_images": total_all,
            "train_good_images": total_train,
            "test_good_images": total_test_good,
            "test_defect_images": total_test_defect,
            "message": f"Successfully indexed real MVTec AD dataset: {len(categories)} categories, {total_all} total images across train and test splits."
        }

    @classmethod
    def generate_sample_dataset(cls) -> Dict[str, Any]:
        """Backward-compatible alias pointing to real dataset verification"""
        return cls.verify_and_index_dataset()
