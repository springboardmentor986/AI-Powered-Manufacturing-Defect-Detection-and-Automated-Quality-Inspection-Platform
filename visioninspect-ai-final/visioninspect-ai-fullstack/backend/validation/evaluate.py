"""
Milestone 4 - Run the real detection pipeline against the labeled synthetic
dataset and compute precision, recall, F1, per-class average precision, mAP,
and a confusion matrix, using IoU to match predictions to ground truth.

Caveat (also surfaced in the API response and the UI): this proves the
detection + scoring logic is internally consistent on generated images. It
is NOT a production accuracy guarantee on real factory photos.
"""
from collections import defaultdict
from app.cv_pipeline import detect_defects
from app.severity import score_defect

IOU_MATCH_THRESHOLD = 0.3


def iou(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax+aw, bx+bw), min(ay+ah, by+bh)
    iw, ih = max(0, ix2-ix1), max(0, iy2-iy1)
    inter = iw * ih
    union = aw*ah + bw*bh - inter
    return inter / union if union > 0 else 0.0


def evaluate(dataset: list[dict]) -> dict:
    tp = fp = fn = 0
    per_class = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    confusion = defaultdict(lambda: defaultdict(int))  # confusion[true][predicted] += 1

    for item in dataset:
        img, gts = item["image"], item["ground_truth"]
        h, w = img.shape
        raw = detect_defects(img)
        preds = [score_defect(d, w, h) for d in raw]
        matched_gt = set()

        for p in preds:
            pbox = (p["bbox_x"], p["bbox_y"], p["bbox_w"], p["bbox_h"])
            best_iou, best_idx = 0, -1
            for idx, g in enumerate(gts):
                if idx in matched_gt:
                    continue
                score = iou(pbox, g["bbox"])
                if score > best_iou:
                    best_iou, best_idx = score, idx
            if best_iou >= IOU_MATCH_THRESHOLD:
                matched_gt.add(best_idx)
                true_type = gts[best_idx]["defect_type"]
                confusion[true_type][p["defect_type"]] += 1
                if p["defect_type"] == true_type:
                    tp += 1; per_class[true_type]["tp"] += 1
                else:
                    fp += 1; per_class[p["defect_type"]]["fp"] += 1
                    per_class[true_type]["fn"] += 1
            else:
                fp += 1; per_class[p["defect_type"]]["fp"] += 1

        for idx, g in enumerate(gts):
            if idx not in matched_gt:
                fn += 1; per_class[g["defect_type"]]["fn"] += 1

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    per_class_ap = {}
    for cls, c in per_class.items():
        p = c["tp"] / (c["tp"] + c["fp"]) if (c["tp"] + c["fp"]) else 1.0
        r = c["tp"] / (c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) else 1.0
        per_class_ap[cls] = round((p + r) / 2, 3)  # simplified single-point AP (one confidence threshold)

    mAP = round(sum(per_class_ap.values()) / len(per_class_ap), 3) if per_class_ap else 1.0

    return {
        "n_images": len(dataset),
        "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
        "mAP": mAP, "per_class_ap": per_class_ap,
        "confusion_matrix": {k: dict(v) for k, v in confusion.items()},
    }


if __name__ == "__main__":
    import json
    from generate_labeled_dataset import generate_dataset
    ds = generate_dataset(n_images=125, seed=42)
    print(json.dumps(evaluate(ds), indent=2))
