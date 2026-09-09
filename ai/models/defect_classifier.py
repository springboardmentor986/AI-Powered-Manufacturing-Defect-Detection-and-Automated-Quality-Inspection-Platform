import json
from pathlib import Path
from typing import Dict, List, Tuple, Union

import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models import ResNet18_Weights

from ai.models.category_classifier import get_default_device


class HierarchicalDefectClassifier(nn.Module):
    """
    Option B: Hierarchical Category-Conditioned Defect Classifier.
    Extracts 512-dim features with a ResNet18 backbone, then projects through
    a category-specific classification head to predict 'good' or the specific defect type.
    """

    def __init__(
        self,
        defect_classes_dict: Dict[str, List[str]],
        pretrained: bool = True,
    ):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        base = models.resnet18(weights=weights)

        # Backbone without the final FC layer
        self.backbone = nn.Sequential(
            base.conv1,
            base.bn1,
            base.relu,
            base.maxpool,
            base.layer1,
            base.layer2,
            base.layer3,
            base.layer4,
            base.avgpool,
        )

        in_features = base.fc.in_features  # 512
        self.heads = nn.ModuleDict()
        self.defect_classes = defect_classes_dict

        for cat, classes in defect_classes_dict.items():
            self.heads[cat] = nn.Sequential(
                nn.Dropout(p=0.3),
                nn.Linear(in_features, len(classes)),
            )

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.backbone(x)
        return torch.flatten(feat, 1)

    def forward(self, x: torch.Tensor, category: str) -> torch.Tensor:
        feat = self.extract_features(x)
        if category not in self.heads:
            raise ValueError(f"Unknown category '{category}' for defect classification.")
        return self.heads[category](feat)

    def forward_features(self, feat: torch.Tensor, category: str) -> torch.Tensor:
        if category not in self.heads:
            raise ValueError(f"Unknown category '{category}' for defect classification.")
        return self.heads[category](feat)


class GlobalDefectClassifier(nn.Module):
    """
    Option A: Monolithic Global Flat Classifier.
    Maps ResNet18 features to all global unique defect labels (or full flat classes).
    Used as an empirical baseline for comparing Option A vs Option B.
    """

    def __init__(self, num_classes: int, pretrained: bool = True):
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


class DefectInference:
    """
    Inference helper for hierarchical defect-type prediction given an image and category.
    """

    def __init__(
        self,
        model_path: Union[str, Path],
        defect_classes_path: Union[str, Path],
        device: torch.device = None,
    ):
        self.device = device or get_default_device()

        with open(defect_classes_path, "r", encoding="utf-8") as f:
            self.defect_classes: Dict[str, List[str]] = json.load(f)

        self.model = HierarchicalDefectClassifier(
            defect_classes_dict=self.defect_classes,
            pretrained=False,
        )

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
        category: str = None,
        image_path: Union[str, Path, np.ndarray] = None,
        **kwargs,
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Predict defect type for an image given its category.
        Returns:
            predicted_defect: e.g. 'good', 'bent_wire', 'crack', etc.
            confidence: probability score [0.0, 1.0]
            probabilities: dict of all defect classes for this category
        """
        target_img = image_input if image_input is not None else (image_path if image_path is not None else kwargs.get("image_path"))
        if target_img is None:
            raise ValueError("Must provide either image_input or image_path")

        target_category = category if category is not None else kwargs.get("category")
        if target_category not in self.defect_classes:
            raise ValueError(f"Category '{target_category}' is not in known defect classes.")

        tensor = self.preprocess_image(target_img)
        logits = self.model(tensor, target_category)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

        classes = self.defect_classes[target_category]
        pred_idx = int(np.argmax(probs))
        pred_defect = classes[pred_idx]
        confidence = float(probs[pred_idx])

        all_probs = {classes[i]: float(probs[i]) for i in range(len(classes))}
        return pred_defect, confidence, all_probs
