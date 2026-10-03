"""
Milestone 4 - Generate synthetic grayscale "product surface" images with
known, labeled defects (ground truth), so detection accuracy can be measured
objectively (not just eyeballed).
"""
import random
import numpy as np

DEFECT_TYPES = ["crack", "scratch", "dent", "contamination"]
IMG_SIZE = 200

def _draw_crack(canvas, x, y):
    length = random.randint(40, 90)
    angle = random.uniform(0, 3.14)
    x2 = int(x + length * np.cos(angle)); y2 = int(y + length * np.sin(angle))
    steps = max(abs(x2 - x), abs(y2 - y), 1)
    for i in range(steps):
        px = int(x + (x2 - x) * i / steps + random.uniform(-2, 2))
        py = int(y + (y2 - y) * i / steps + random.uniform(-2, 2))
        if 0 <= px < IMG_SIZE and 0 <= py < IMG_SIZE:
            canvas[max(0,py-1):py+2, max(0,px-1):px+2] = 40
    xs = [x, x2]; ys = [y, y2]
    return min(xs), min(ys), max(xs)-min(xs)+4, max(ys)-min(ys)+4

def _draw_scratch(canvas, x, y):
    length = random.randint(30, 70)
    thick = random.randint(1, 2)
    canvas[y:y+thick, x:x+length] = 60
    return x, y, length, thick

def _draw_dent(canvas, x, y):
    r = random.randint(8, 16)
    yy, xx = np.ogrid[:IMG_SIZE, :IMG_SIZE]
    mask = (xx - x) ** 2 + (yy - y) ** 2 <= r * r
    canvas[mask] = 70
    return x - r, y - r, 2 * r, 2 * r

def _draw_contamination(canvas, x, y):
    w, h = random.randint(14, 26), random.randint(14, 26)
    patch = canvas[y:y+h, x:x+w]
    noise = np.random.randint(30, 90, patch.shape, dtype=np.uint8)
    canvas[y:y+h, x:x+w] = noise
    return x, y, w, h

_DRAW = {"crack": _draw_crack, "scratch": _draw_scratch, "dent": _draw_dent, "contamination": _draw_contamination}

def generate_dataset(n_images: int = 25, seed: int | None = None):
    if seed is not None:
        random.seed(seed); np.random.seed(seed)
    dataset = []
    for i in range(n_images):
        canvas = np.full((IMG_SIZE, IMG_SIZE), 180, dtype=np.uint8)
        canvas += np.random.randint(-5, 5, canvas.shape, dtype=np.int16).clip(-5, 5).astype(np.uint8)
        clean = random.random() < 0.15
        ground_truth = []
        if not clean:
            n_defects = random.choice([1, 1, 1, 2])
            for _ in range(n_defects):
                dtype = random.choice(DEFECT_TYPES)
                x, y = random.randint(20, IMG_SIZE - 40), random.randint(20, IMG_SIZE - 40)
                bx, by, bw, bh = _DRAW[dtype](canvas, x, y)
                ground_truth.append({"defect_type": dtype, "bbox": (bx, by, bw, bh)})
        dataset.append({"image": canvas, "ground_truth": ground_truth})
    return dataset
