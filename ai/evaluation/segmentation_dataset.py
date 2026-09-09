import cv2
import numpy as np
import torch
from torch.utils.data import Dataset


class MVTecSegmentationDataset(Dataset):
    """
    Dataset for supervised defect segmentation using MVTec AD.

    Each sample contains:
        image  -> RGB image tensor
        mask   -> binary defect mask tensor

    Images and masks are resized to 224x224.
    """

    def __init__(self, samples, image_size=224):
        self.samples = samples
        self.image_size = image_size

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        image_path, mask_path = self.samples[index]

        # -------------------------
        # Load image
        # -------------------------
        image = cv2.imread(str(image_path))

        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        # OpenCV loads BGR → convert to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Resize image
        image = cv2.resize(
            image,
            (self.image_size, self.image_size),
            interpolation=cv2.INTER_LINEAR,
        )

        # Convert uint8 [0,255] → float32 [0,1]
        image = image.astype(np.float32) / 255.0

        # HWC → CHW
        image = torch.from_numpy(image).permute(2, 0, 1)

        # -------------------------
        # Load ground-truth mask
        # -------------------------
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

        if mask is None:
            raise ValueError(f"Could not read mask: {mask_path}")

        # IMPORTANT:
        # Masks contain categorical pixel values.
        # Therefore use nearest-neighbor interpolation.
        mask = cv2.resize(
            mask,
            (self.image_size, self.image_size),
            interpolation=cv2.INTER_NEAREST,
        )

        # Convert to binary:
        # 0       → normal pixel
        # > 0     → defect pixel
        mask = (mask > 0).astype(np.float32)

        # Add channel dimension:
        # [H,W] → [1,H,W]
        mask = torch.from_numpy(mask).unsqueeze(0)

        return image, mask