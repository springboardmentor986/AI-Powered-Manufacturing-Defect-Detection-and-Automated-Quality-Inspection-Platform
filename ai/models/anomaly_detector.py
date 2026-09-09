from pathlib import Path

import cv2
import numpy as np
import torch
from torchvision import models


class AnomalyDetector:
    def __init__(self, normal_features_path: str):
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        base_model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.model = torch.nn.Sequential(
            base_model.conv1,
            base_model.bn1,
            base_model.relu,
            base_model.maxpool,
            base_model.layer1,
            base_model.layer2,
            base_model.layer3,
        ).to(self.device)
        self.model.eval()

        self.normal_features = torch.load(
            normal_features_path,
            map_location=self.device,
            weights_only=True,
        )

    def preprocess(self, image_path: str):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        original_height, original_width = image.shape[:2]
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (224, 224)).astype(np.float32) / 255.0
        tensor = torch.from_numpy(resized).permute(2, 0, 1).unsqueeze(0).to(self.device)

        return tensor, original_height, original_width

    def extract_features(self, image: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            feature_map = self.model(image)

        # [B, C, H, W] -> [B, H*W, C]
        feature_map = feature_map.permute(0, 2, 3, 1)
        batch_size, height, width, channels = feature_map.shape
        return feature_map.reshape(batch_size, height * width, channels)

    def calculate_anomaly_map(self, features: torch.Tensor) -> torch.Tensor:
        distances = torch.cdist(features[0], self.normal_features)
        nearest_distances = distances.min(dim=1).values
        return nearest_distances.reshape(14, 14)

    def calculate_anomaly_score(self, anomaly_map: torch.Tensor) -> float:
        # Score is the mean of the top 10% most anomalous patches (19 of 196)
        top_k = max(1, int(anomaly_map.numel() * 0.10))
        top_values = torch.topk(anomaly_map.flatten(), k=top_k).values
        return float(top_values.mean().item())

    def create_heatmap(self, anomaly_map: np.ndarray, original_height: int, original_width: int) -> np.ndarray:
        return cv2.resize(
            anomaly_map.astype(np.float32),
            (original_width, original_height),
            interpolation=cv2.INTER_LINEAR,
        )

    def predict(self, image_path: str) -> dict:
        image, original_height, original_width = self.preprocess(image_path)
        features = self.extract_features(image)
        anomaly_map = self.calculate_anomaly_map(features)
        anomaly_score = self.calculate_anomaly_score(anomaly_map)
        heatmap = self.create_heatmap(
            anomaly_map.cpu().numpy(),
            original_height,
            original_width,
        )

        return {
            "image_path": str(Path(image_path)),
            "anomaly_score": anomaly_score,
            "anomaly_map": anomaly_map.cpu().numpy(),
            "heatmap": heatmap,
            "original_height": original_height,
            "original_width": original_width,
        }