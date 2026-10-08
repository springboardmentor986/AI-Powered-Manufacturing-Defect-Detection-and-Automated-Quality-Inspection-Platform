"""
Convolutional autoencoder for anomaly detection (Milestone 4 upgrade).

Trained per product category on only the 'good' (normal) training
images. At inference, a defect region reconstructs poorly compared to
the surrounding normal-looking areas, producing a spatial error map
that's more discriminative than the Milestone 2 statistical baseline
(fixed per-pixel mean/std deviation).

Input: 128x128 grayscale image, normalized to [0, 1].

Bottleneck sizing matters here: the encoder must compress the image into
a meaningfully smaller representation than the input, or the network can
just learn a near-identity mapping and reconstruct defects just as well
as normal regions (which defeats the purpose of anomaly detection). This
architecture compresses 128x128 (16,384 values) down to 32 channels at
8x8 (2,048 values) — an 8x reduction — forcing the network to learn a
compact representation of what 'normal' looks like for that category.
"""

import torch.nn as nn


class ConvAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 8, 3, stride=2, padding=1),    # 128 -> 64
            nn.ReLU(True),
            nn.Conv2d(8, 16, 3, stride=2, padding=1),   # 64 -> 32
            nn.ReLU(True),
            nn.Conv2d(16, 32, 3, stride=2, padding=1),  # 32 -> 16
            nn.ReLU(True),
            nn.Conv2d(32, 32, 3, stride=2, padding=1),  # 16 -> 8
            nn.ReLU(True),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(32, 32, 3, stride=2, padding=1, output_padding=1),  # 8 -> 16
            nn.ReLU(True),
            nn.ConvTranspose2d(32, 16, 3, stride=2, padding=1, output_padding=1),  # 16 -> 32
            nn.ReLU(True),
            nn.ConvTranspose2d(16, 8, 3, stride=2, padding=1, output_padding=1),   # 32 -> 64
            nn.ReLU(True),
            nn.ConvTranspose2d(8, 1, 3, stride=2, padding=1, output_padding=1),    # 64 -> 128
            nn.Sigmoid(),
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z)
