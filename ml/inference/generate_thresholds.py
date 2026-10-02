import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import json
import numpy as np
import torch
import torch.nn as nn

from preprocessing.preprocess import preprocess_image

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "saved_models"
OUTPUT_FILE = BASE_DIR / "inference" / "thresholds.json"

CATEGORIES = [
    "bottle","cable","capsule","carpet","grid",
    "hazelnut","leather","metal_nut","pill","screw",
    "tile","toothbrush","transistor","wood","zipper"
]
IMAGE_SIZE = (224, 224)

class ConvAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3,32,3,stride=2,padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
            nn.Conv2d(32,64,3,stride=2,padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
            nn.Conv2d(64,128,3,stride=2,padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True),
            nn.Conv2d(128,256,3,stride=2,padding=1), nn.BatchNorm2d(256), nn.ReLU(inplace=True),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(256,128,3,stride=2,padding=1,output_padding=1),
            nn.BatchNorm2d(128), nn.ReLU(inplace=True),
            nn.ConvTranspose2d(128,64,3,stride=2,padding=1,output_padding=1),
            nn.BatchNorm2d(64), nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64,32,3,stride=2,padding=1,output_padding=1),
            nn.BatchNorm2d(32), nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32,3,3,stride=2,padding=1,output_padding=1),
            nn.Sigmoid(),
        )
    def forward(self,x):
        return self.decoder(self.encoder(x))

def load_model(category):
    path = MODEL_DIR / f"{category}_autoencoder.pth"
    if not path.exists():
        raise FileNotFoundError(path)
    model = ConvAutoencoder()
    checkpoint = torch.load(path, map_location="cpu")
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        checkpoint = checkpoint["model_state_dict"]
    model.load_state_dict(checkpoint)
    model.eval()
    return model

def image_to_tensor(image_path):
    normalized, _ = preprocess_image(image_path)
    if normalized.shape != (224,224,3):
        raise ValueError(f"Unexpected shape: {normalized.shape}")
    return torch.from_numpy(np.transpose(normalized,(2,0,1))).float().unsqueeze(0)

@torch.no_grad()
def reconstruction_error(model, image_path):
    x=image_to_tensor(image_path)
    y=model(x)
    return float(torch.mean((x-y)**2).item())

def generate_category_threshold(category):
    model=load_model(category)
    good_dir=DATASET_DIR/category/"train"/"good"
    images=sorted(good_dir.glob("*"))
    errors=[]
    for path in images:
        try:
            errors.append(reconstruction_error(model,path))
        except Exception as e:
            print(f"Skipped {path.name}: {e}")
    if not errors:
        raise RuntimeError(f"No valid images for {category}")
    return {
        "threshold": float(np.percentile(errors,99)),
        "num_good_images": len(errors),
        "method": "99th_percentile_training_good",
        "preprocessing": "resize -> RGB -> bilateral denoise -> CLAHE -> normalize",
        "image_size": list(IMAGE_SIZE)
    }

def main():
    OUTPUT_FILE.parent.mkdir(parents=True,exist_ok=True)
    thresholds={}
    print("\nGENERATING AUTOENCODER THRESHOLDS")
    print("="*90)
    print("Preprocessing: resize -> RGB -> bilateral denoise -> CLAHE -> normalize")
    print("Threshold: 99th percentile of training-good reconstruction errors")
    print("="*90)
    for category in CATEGORIES:
        try:
            result=generate_category_threshold(category)
            thresholds[category]=result
            print(f"{category.upper():12s} | threshold={result['threshold']:.8f} | images={result['num_good_images']}")
        except Exception as e:
            print(f"{category.upper():12s} | ERROR: {e}")
    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
        json.dump(thresholds,f,indent=2)
    print("="*90)
    print(f"Saved thresholds to: {OUTPUT_FILE}")
    print("Threshold generation completed.")

if __name__=="__main__":
    main()
