import json
from pathlib import Path
from typing import Dict, List, Tuple, Union

import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models import ResNet18_Weights


def get_default_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")


class CategoryClassifier(nn.Module):
    """
    ResNet18-based 15-class Category Classifier for MVTec products.
    """

    def __init__(self, num_classes: int = 15, pretrained: bool = True):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        self.backbone = models.resnet18(weights=weights)
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


class CategoryInference:
    """
    Inference helper for category prediction with pre-processing and class mapping.
    """

    def __init__(
        self,
        model_path: Union[str, Path],
        classes_path: Union[str, Path],
        device: torch.device = None,
    ):
        self.device = device or get_default_device()

        with open(classes_path, "r", encoding="utf-8") as f:
            self.classes: List[str] = json.load(f)

        self.model = CategoryClassifier(num_classes=len(self.classes), pretrained=False)
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)
        if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            self.model.load_state_dict(checkpoint["state_dict"])
        elif isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            self.model.load_state_dict(checkpoint["model_state_dict"])
        else:
            self.model.load_state_dict(checkpoint)

        self.model.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

    def preprocess_image(self, image_input: Union[str, Path, np.ndarray, Image.Image]) -> torch.Tensor:
        if isinstance(image_input, (str, Path)):
            pil_image = Image.open(str(image_input)).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_image = image_input.convert("RGB")
        elif isinstance(image_input, np.ndarray):
            pil_image = Image.fromarray(image_input)
        else:
            raise ValueError(f"Could not load image from {image_input}")

        pil_image = pil_image.resize((224, 224), Image.Resampling.BILINEAR)
        tensor = self.transform(pil_image).unsqueeze(0)
        return tensor.to(self.device)

    @torch.no_grad()
    def predict(
        self,
        image_input: Union[str, Path, np.ndarray] = None,
        image_path: Union[str, Path, np.ndarray] = None,
        **kwargs,
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Returns:
            predicted_category: Name of the predicted category
            confidence: Probability score [0.0, 1.0]
            probabilities: Dict mapping all 15 categories to their probabilities
        """
        target_img = image_input if image_input is not None else (image_path if image_path is not None else kwargs.get("image_path"))
        if target_img is None:
            raise ValueError("Must provide either image_input or image_path")

        tensor = self.preprocess_image(target_img)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

        pred_idx = int(np.argmax(probs))
        pred_category = self.classes[pred_idx]
        confidence = float(probs[pred_idx])

        all_probs = {self.classes[i]: float(probs[i]) for i in range(len(self.classes))}
        return pred_category, confidence, all_probs
