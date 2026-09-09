import csv
import json
import time
from pathlib import Path
from typing import Dict, List

import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from torchvision.models import ResNet18_Weights

from ai.models.category_classifier import get_default_device

CACHE_DIR = Path("ai/models/features_cache")


class FeatureDataset(Dataset):
    def __init__(
        self,
        csv_path: str,
        category_to_idx: dict,
        defect_classes: Dict[str, List[str]],
        global_class_to_idx: dict,
        transform=None,
    ):
        self.samples = []
        self.transform = transform

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cat = row["category"]
                defect = row["defect_type"]
                cat_idx = category_to_idx[cat]
                local_defect_idx = defect_classes[cat].index(defect)
                global_idx = global_class_to_idx[f"{cat}__{defect}"]

                self.samples.append({
                    "image_path": row["image_path"],
                    "category": cat,
                    "cat_idx": cat_idx,
                    "defect_type": defect,
                    "local_defect_idx": local_defect_idx,
                    "global_idx": global_idx,
                    "is_defective": int(row["is_defective"]),
                })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        image = Image.open(item["image_path"]).convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
        if self.transform:
            image = self.transform(image)
        return (
            image,
            item["cat_idx"],
            item["category"],
            item["local_defect_idx"],
            item["global_idx"],
            item["is_defective"],
            item["image_path"],
        )


def collate_features(batch):
    images = torch.stack([b[0] for b in batch], dim=0)
    cat_indices = torch.tensor([b[1] for b in batch], dtype=torch.long)
    categories = [b[2] for b in batch]
    local_indices = torch.tensor([b[3] for b in batch], dtype=torch.long)
    global_indices = torch.tensor([b[4] for b in batch], dtype=torch.long)
    is_defective = torch.tensor([b[5] for b in batch], dtype=torch.long)
    image_paths = [b[6] for b in batch]
    return images, cat_indices, categories, local_indices, global_indices, is_defective, image_paths


def extract_and_cache_features():
    device = get_default_device()
    print(f"Extracting ResNet18 features on device: {device}", flush=True)

    with open("ai/models/category_classes.json", "r", encoding="utf-8") as f:
        categories = json.load(f)
    category_to_idx = {c: i for i, c in enumerate(categories)}

    with open("ai/models/defect_classes.json", "r", encoding="utf-8") as f:
        defect_classes = json.load(f)

    all_global_classes = []
    for cat, defs in defect_classes.items():
        for d in defs:
            all_global_classes.append(f"{cat}__{d}")
    global_class_to_idx = {c: i for i, c in enumerate(all_global_classes)}

    # Save global class list
    with open("ai/models/defect_global_classes.json", "w", encoding="utf-8") as f:
        json.dump(all_global_classes, f, indent=2)

    # Feature extractor backbone
    weights = ResNet18_Weights.DEFAULT
    base = models.resnet18(weights=weights)
    backbone = nn.Sequential(
        base.conv1, base.bn1, base.relu, base.maxpool,
        base.layer1, base.layer2, base.layer3, base.layer4,
        base.avgpool
    ).to(device).eval()

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    for split_name in ["train", "val"]:
        csv_path = f"ai/evaluation/classification_splits/{split_name}.csv"
        out_pt = CACHE_DIR / f"{split_name}_features.pt"

        if out_pt.exists():
            print(f"Features already exist at {out_pt}, skipping.", flush=True)
            continue

        dataset = FeatureDataset(csv_path, category_to_idx, defect_classes, global_class_to_idx, transform=transform)
        loader = DataLoader(dataset, batch_size=64, shuffle=False, collate_fn=collate_features, num_workers=0)

        all_feats = []
        all_cat_idxs = []
        all_categories = []
        all_local_idxs = []
        all_global_idxs = []
        all_is_defective = []
        all_paths = []

        total_batches = len(loader)
        start_t = time.time()
        print(f"Extracting features for {split_name} ({len(dataset)} images)...", flush=True)

        with torch.no_grad():
            for b_idx, (imgs, cat_idxs, cats, local_idxs, global_idxs, is_def, paths) in enumerate(loader):
                imgs = imgs.to(device)
                feat = backbone(imgs)
                feat = torch.flatten(feat, 1).cpu()

                all_feats.append(feat)
                all_cat_idxs.append(cat_idxs)
                all_categories.extend(cats)
                all_local_idxs.append(local_idxs)
                all_global_idxs.append(global_idxs)
                all_is_defective.append(is_def)
                all_paths.extend(paths)

                if (b_idx + 1) % 10 == 0 or (b_idx + 1) == total_batches:
                    elapsed = time.time() - start_t
                    processed = min((b_idx + 1) * 64, len(dataset))
                    print(f"  [{split_name}] {processed}/{len(dataset)} images ({elapsed:.1f}s, {processed / elapsed:.1f} img/s)", flush=True)

        cached_data = {
            "features": torch.cat(all_feats, dim=0),
            "cat_indices": torch.cat(all_cat_idxs, dim=0),
            "categories": all_categories,
            "local_indices": torch.cat(all_local_idxs, dim=0),
            "global_indices": torch.cat(all_global_idxs, dim=0),
            "is_defective": torch.cat(all_is_defective, dim=0),
            "image_paths": all_paths,
        }

        torch.save(cached_data, out_pt)
        print(f"Successfully cached {len(cached_data['features'])} features to {out_pt} ({time.time() - start_t:.1f}s total)", flush=True)


if __name__ == "__main__":
    extract_and_cache_features()
