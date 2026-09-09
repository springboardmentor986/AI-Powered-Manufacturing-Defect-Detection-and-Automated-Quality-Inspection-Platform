import csv
import json
import random
from pathlib import Path
from collections import defaultdict

# ============================================================
# Configuration
# ============================================================

DATASET_ROOT = Path("mvtec_anomaly_detection")
SPLITS_DIR = Path("ai/evaluation/classification_splits")
MODELS_DIR = Path("ai/models")

RANDOM_SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


def collect_all_samples():
    """
    Scans mvtec_anomaly_detection for all images across all 15 categories:
    - Normal images from train/good and test/good (defect_type = 'good')
    - Defective images from test/<defect_type>
    Returns:
        samples: list of dicts with {category, defect_type, image_path, is_defective}
        categories: sorted list of 15 categories
        defect_classes_per_category: dict mapping category -> sorted list of defect names (with 'good' first)
    """
    samples = []
    categories = sorted([
        d.name for d in DATASET_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])
    
    defect_classes_per_category = {}

    for category in categories:
        cat_dir = DATASET_ROOT / category
        cat_defects = set()
        cat_defects.add("good")

        # 1. Normal train images (train/good)
        train_good_dir = cat_dir / "train" / "good"
        if train_good_dir.exists():
            for img_p in sorted(train_good_dir.glob("*.png")):
                samples.append({
                    "category": category,
                    "defect_type": "good",
                    "image_path": str(img_p),
                    "is_defective": 0,
                })

        # 2. Test directory (contains both 'good' and defect folders)
        test_dir = cat_dir / "test"
        if test_dir.exists():
            for sub_dir in sorted(test_dir.iterdir()):
                if not sub_dir.is_dir() or sub_dir.name.startswith("."):
                    continue
                d_name = sub_dir.name
                cat_defects.add(d_name)
                is_def = 0 if d_name == "good" else 1

                for img_p in sorted(sub_dir.glob("*.png")):
                    samples.append({
                        "category": category,
                        "defect_type": d_name,
                        "image_path": str(img_p),
                        "is_defective": is_def,
                    })

        # Ensure 'good' is always at index 0, followed by alphabetical defect names
        other_defects = sorted([d for d in cat_defects if d != "good"])
        defect_classes_per_category[category] = ["good"] + other_defects

    return samples, categories, defect_classes_per_category


def create_splits():
    random.seed(RANDOM_SEED)
    samples, categories, defect_classes_per_category = collect_all_samples()

    # Group by (category, defect_type)
    groups = defaultdict(list)
    for s in samples:
        groups[(s["category"], s["defect_type"])].append(s)

    train_set = []
    val_set = []
    test_set = []

    for group_key, group_samples in sorted(groups.items()):
        random.shuffle(group_samples)
        n = len(group_samples)

        if n == 1:
            # Single sample: put in train
            train_set.extend(group_samples)
        elif n == 2:
            train_set.append(group_samples[0])
            test_set.append(group_samples[1])
        else:
            n_train = int(round(n * TRAIN_RATIO))
            n_val = int(round(n * VAL_RATIO))
            
            # Ensure at least 1 in train and test if n >= 3
            if n_train == 0:
                n_train = 1
            if n_val == 0:
                n_val = 1
            if n_train + n_val >= n:
                n_train = n - 2
                n_val = 1

            n_test = n - (n_train + n_val)
            if n_test <= 0:
                n_test = 1
                if n_train > 1:
                    n_train -= 1
                else:
                    n_val -= 1

            train_set.extend(group_samples[:n_train])
            val_set.extend(group_samples[n_train:n_train + n_val])
            test_set.extend(group_samples[n_train + n_val:])

    # Shuffle final splits
    random.shuffle(train_set)
    random.shuffle(val_set)
    random.shuffle(test_set)

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = ["category", "defect_type", "image_path", "is_defective"]

    for split_name, split_data in [
        ("train.csv", train_set),
        ("val.csv", val_set),
        ("test.csv", test_set),
    ]:
        out_file = SPLITS_DIR / split_name
        with open(out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(split_data)
        print(f"Saved {len(split_data)} samples to {out_file}")

    # Save class mappings
    cat_file = MODELS_DIR / "category_classes.json"
    with open(cat_file, "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2)
    print(f"Saved {len(categories)} categories to {cat_file}")

    defect_file = MODELS_DIR / "defect_classes.json"
    with open(defect_file, "w", encoding="utf-8") as f:
        json.dump(defect_classes_per_category, f, indent=2)
    print(f"Saved defect classes mapping for {len(defect_classes_per_category)} categories to {defect_file}")


if __name__ == "__main__":
    create_splits()
