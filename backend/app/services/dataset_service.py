import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from ..config import settings

class DatasetService:
    @staticmethod
    def get_mvtec_dir() -> Path:
        return settings.ACTIVE_DATASET_DIR

    @classmethod
    def get_available_categories(cls) -> List[Dict[str, Any]]:
        """Return list of all 15 MVTec AD categories with their counts and status"""
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
                    train_count = len([f for f in train_good_path.glob("*.png")])

                # Count test
                test_path = cat_path / "test"
                if test_path.exists():
                    for item in test_path.iterdir():
                        if item.is_dir():
                            png_count = len([f for f in item.glob("*.png")])
                            if item.name == "good":
                                test_good_count += png_count
                            else:
                                test_defect_count += png_count
                                defect_types.append(item.name)

                # Ground truth check
                gt_path = cat_path / "ground_truth"
                if gt_path.exists() and any(gt_path.iterdir()):
                    has_ground_truth = True

            categories_data.append({
                "category": cat_name,
                "is_loaded": (train_count + test_good_count + test_defect_count) > 0,
                "train_images": train_count,
                "test_good_images": test_good_count,
                "test_defect_images": test_defect_count,
                "total_images": train_count + test_good_count + test_defect_count,
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
            splits["train"]["good"] = [
                f"/static/mvtec/{category}/train/good/{f.name}"
                for f in sorted(train_good.glob("*.png"))[:12]
            ]

        # Test
        test_dir = cat_path / "test"
        if test_dir.exists():
            for defect_dir in test_dir.iterdir():
                if defect_dir.is_dir():
                    splits["test"][defect_dir.name] = [
                        f"/static/mvtec/{category}/test/{defect_dir.name}/{f.name}"
                        for f in sorted(defect_dir.glob("*.png"))[:12]
                    ]

        # Ground truth
        gt_dir = cat_path / "ground_truth"
        if gt_dir.exists():
            for defect_dir in gt_dir.iterdir():
                if defect_dir.is_dir():
                    splits["ground_truth"][defect_dir.name] = [
                        f"/static/mvtec/{category}/ground_truth/{defect_dir.name}/{f.name}"
                        for f in sorted(defect_dir.glob("*.png"))[:12]
                    ]

        return {
            "category": category,
            "found": True,
            "splits": splits
        }

    @classmethod
    def generate_sample_dataset(cls) -> Dict[str, Any]:
        """
        Creates MVTec AD folder structure and generates synthetic industrial images
        for all 15 categories with realistic textures, defects, and ground-truth masks.
        """
        mvtec_root = cls.get_mvtec_dir()
        mvtec_root.mkdir(parents=True, exist_ok=True)

        category_defect_map = {
            "bottle": ["broken_large", "broken_small", "contamination"],
            "cable": ["bent_wire", "cut_inner_insulation", "poke_insulation"],
            "capsule": ["crack", "faulty_imprint", "scratch", "squeeze"],
            "carpet": ["color", "cut", "hole", "thread"],
            "grid": ["bent", "broken", "glue", "metal_contamination"],
            "hazelnut": ["crack", "cut", "hole", "print"],
            "leather": ["color", "cut", "fold", "glue", "poke"],
            "metal_nut": ["bent", "color", "flip", "scratch"],
            "pill": ["color", "combined", "crack", "faulty_imprint", "scratch"],
            "screw": ["manipulated_front", "scratch_head", "scratch_neck", "thread_side"],
            "tile": ["crack", "glue_strip", "gray_stroke", "oil", "rough"],
            "toothbrush": ["defective"],
            "transistor": ["bent_lead", "cut_lead", "damaged_case", "misplaced"],
            "wood": ["color", "hole", "liquid", "scratch"],
            "zipper": ["broken_teeth", "combined", "fabric_border", "split_teeth"]
        }

        generated_counts = {}

        for cat_name, defects in category_defect_map.items():
            cat_dir = mvtec_root / cat_name
            train_good_dir = cat_dir / "train" / "good"
            test_good_dir = cat_dir / "test" / "good"
            
            train_good_dir.mkdir(parents=True, exist_ok=True)
            test_good_dir.mkdir(parents=True, exist_ok=True)

            # Generate train good samples (3 images each)
            for i in range(3):
                img = cls._synthesize_image(cat_name, defect_type="good", index=i)
                img.save(train_good_dir / f"{i:03d}.png")

            # Generate test good samples (2 images each)
            for i in range(2):
                img = cls._synthesize_image(cat_name, defect_type="good", index=i + 10)
                img.save(test_good_dir / f"{i:03d}.png")

            # Generate test defects & ground truth masks (2 images per defect type)
            for defect in defects:
                test_defect_dir = cat_dir / "test" / defect
                gt_defect_dir = cat_dir / "ground_truth" / defect
                test_defect_dir.mkdir(parents=True, exist_ok=True)
                gt_defect_dir.mkdir(parents=True, exist_ok=True)

                for i in range(2):
                    img, mask = cls._synthesize_image(cat_name, defect_type=defect, index=i, return_mask=True)
                    img.save(test_defect_dir / f"{i:03d}.png")
                    mask.save(gt_defect_dir / f"{i:03d}_mask.png")

            generated_counts[cat_name] = {
                "train_good": 3,
                "test_good": 2,
                "defects": len(defects) * 2
            }

        return {
            "status": "SUCCESS",
            "message": "Generated synthetic MVTec AD sample dataset across 15 categories.",
            "categories": generated_counts
        }

    @classmethod
    def _synthesize_image(
        cls,
        category: str,
        defect_type: str = "good",
        index: int = 0,
        return_mask: bool = False
    ) -> Any:
        """Synthesize realistic industrial textures and defects procedurally"""
        width, height = 512, 512
        rng = random.Random(hash(f"{category}_{defect_type}_{index}"))

        # Base Image Generation by Category
        if category in ["carpet", "grid", "tile", "wood", "leather"]:
            # Texture categories
            img, mask = cls._generate_texture_surface(category, rng, width, height)
        else:
            # Object categories (bottle, capsule, pill, screw, metal_nut, etc.)
            img, mask = cls._generate_object_surface(category, rng, width, height)

        # Apply Defect if requested
        if defect_type != "good":
            img, mask = cls._apply_synthetic_defect(img, mask, category, defect_type, rng)

        if return_mask:
            return img, mask
        return img

    @staticmethod
    def _generate_texture_surface(category: str, rng: random.Random, width: int, height: int):
        img = Image.new("RGB", (width, height), (30, 30, 35))
        draw = ImageDraw.Draw(img)
        mask = Image.new("L", (width, height), 0)

        if category == "wood":
            # Wood grain patterns
            base_col = (180, 130, 80)
            for y in range(height):
                var = int(25 * np.sin(y / 15.0) + rng.randint(-8, 8))
                r = max(0, min(255, base_col[0] + var))
                g = max(0, min(255, base_col[1] + var // 2))
                b = max(0, min(255, base_col[2] + var // 3))
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        elif category == "tile":
            # Smooth ceramic tile with slight noise
            for y in range(0, height, 4):
                for x in range(0, width, 4):
                    val = 210 + rng.randint(-15, 15)
                    draw.rectangle([x, y, x+4, y+4], fill=(val, val + 2, val - 3))
        elif category == "leather":
            # Organic speckled leather grain
            for y in range(0, height, 6):
                for x in range(0, width, 6):
                    c = 110 + rng.randint(-20, 20)
                    draw.ellipse([x, y, x+5, y+5], fill=(c+15, c, c-10))
        elif category == "grid":
            # Metallic grid / mesh
            draw.rectangle([0, 0, width, height], fill=(45, 45, 50))
            for x in range(0, width, 32):
                draw.line([(x, 0), (x, height)], fill=(160, 160, 175), width=3)
            for y in range(0, height, 32):
                draw.line([(0, y), (width, y)], fill=(160, 160, 175), width=3)
        elif category == "carpet":
            # Woven fiber pattern
            for y in range(0, height, 3):
                c = 90 + int(30 * np.sin(y / 4.0)) + rng.randint(-10, 10)
                draw.line([(0, y), (width, y)], fill=(c, c + 20, c + 40))

        return img, mask

    @staticmethod
    def _generate_object_surface(category: str, rng: random.Random, width: int, height: int):
        # Dark clean industrial background
        img = Image.new("RGB", (width, height), (22, 24, 29))
        draw = ImageDraw.Draw(img)
        mask = Image.new("L", (width, height), 0)

        cx, cy = width // 2, height // 2

        if category == "bottle":
            # Glass bottle silhouette
            draw.rectangle([cx - 50, cy - 140, cx + 50, cy + 150], fill=(70, 110, 100), outline=(130, 180, 170), width=3)
            draw.rectangle([cx - 20, cy - 190, cx + 20, cy - 140], fill=(60, 95, 90), outline=(110, 160, 150), width=2)
            draw.rectangle([cx - 25, cy - 210, cx + 25, cy - 190], fill=(190, 160, 60)) # Cap
        elif category == "capsule" or category == "pill":
            # Dual color pharma capsule
            draw.rounded_rectangle([cx - 60, cy - 130, cx + 60, cy], radius=60, fill=(220, 50, 50))
            draw.rounded_rectangle([cx - 60, cy, cx + 60, cy + 130], radius=60, fill=(240, 240, 245))
        elif category == "screw":
            # Metallic screw
            draw.rectangle([cx - 20, cy - 100, cx + 20, cy + 160], fill=(160, 165, 175))
            draw.ellipse([cx - 65, cy - 170, cx + 65, cy - 100], fill=(185, 190, 200), outline=(100, 105, 115), width=3)
            for y in range(cy - 70, cy + 150, 20):
                draw.line([(cx - 25, y), (cx + 25, y + 10)], fill=(90, 95, 105), width=4)
        elif category == "metal_nut":
            # Hexagonal nut
            points = [
                (cx, cy - 130), (cx + 115, cy - 65), (cx + 115, cy + 65),
                (cx, cy + 130), (cx - 115, cy + 65), (cx - 115, cy - 65)
            ]
            draw.polygon(points, fill=(165, 170, 180), outline=(90, 95, 105))
            draw.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], fill=(22, 24, 29), outline=(80, 85, 95), width=5)
        elif category == "transistor":
            # Electronic component
            draw.rectangle([cx - 70, cy - 80, cx + 70, cy + 60], fill=(45, 45, 50), outline=(80, 80, 85), width=2)
            for lx in [cx - 40, cx, cx + 40]:
                draw.line([(lx, cy + 60), (lx, cy + 170)], fill=(190, 190, 200), width=6)
        else:
            # Default industrial circular part
            draw.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], fill=(120, 130, 145), outline=(180, 190, 210), width=4)

        return img, mask

    @staticmethod
    def _apply_synthetic_defect(img: Image.Image, mask: Image.Image, category: str, defect_type: str, rng: random.Random):
        draw = ImageDraw.Draw(img)
        mask_draw = ImageDraw.Draw(mask)
        w, h = img.size
        cx, cy = w // 2 + rng.randint(-30, 30), h // 2 + rng.randint(-30, 30)

        if "scratch" in defect_type or "crack" in defect_type or "cut" in defect_type:
            # Linear jagged scratch
            points = [(cx + rng.randint(-60, 60), cy + rng.randint(-60, 60))]
            for _ in range(5):
                points.append((points[-1][0] + rng.randint(-25, 25), points[-1][1] + rng.randint(-25, 25)))
            draw.line(points, fill=(240, 40, 40) if "color" not in defect_type else (30, 30, 30), width=4)
            mask_draw.line(points, fill=255, width=6)

        elif "hole" in defect_type or "broken" in defect_type or "dent" in defect_type:
            # Dark puncture / missing chunk
            r = rng.randint(20, 45)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(15, 15, 18), outline=(200, 50, 50), width=2)
            mask_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)

        elif "color" in defect_type or "contamination" in defect_type or "oil" in defect_type or "liquid" in defect_type:
            # Smudge / stain
            r = rng.randint(25, 50)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(180, 40, 40))
            mask_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)

        else:
            # Generic anomaly patch
            draw.rectangle([cx - 30, cy - 30, cx + 30, cy + 30], fill=(220, 80, 20))
            mask_draw.rectangle([cx - 30, cy - 30, cx + 30, cy + 30], fill=255)

        return img, mask
