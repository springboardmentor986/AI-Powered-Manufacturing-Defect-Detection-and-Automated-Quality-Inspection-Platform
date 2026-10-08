"""
Milestone 4 — Detection accuracy validation.

Evaluates the defect detection engine against the MVTec AD dataset's own
ground-truth labels: every image under a category's test/good/ folder is
genuinely normal, and every image under any other test/<defect_type>/
folder is genuinely defective. This gives an honest, independent accuracy
measurement (nothing in the test set was used to train/build the model).

Note: this validates DETECTION accuracy (normal vs defective) — the
model's real prediction. It does NOT validate defect TYPE classification
accuracy, because type labels for dataset images are read directly from
the folder name (see update_defect_labels.py), not predicted by a
classifier.

Usage (from the backend project root, with venv active):
    python evaluate_accuracy.py
    python evaluate_accuracy.py --limit 50   # faster, fewer images/category
"""

import argparse
from pathlib import Path

from app.vision import detector

DATASET_IMAGES_DIR = Path("dataset_images")
RESULTS_DIR = Path("results")


def evaluate_category(category_name: str, test_dir: Path, limit: int | None):
    tp = fp = tn = fn = 0
    errors = 0

    for defect_folder in sorted(test_dir.iterdir()):
        if not defect_folder.is_dir():
            continue

        ground_truth = "normal" if defect_folder.name == "good" else "defective"
        image_paths = sorted(defect_folder.glob("*.png"))
        if limit:
            image_paths = image_paths[:limit]

        for img_path in image_paths:
            try:
                prediction = detector.predict(str(img_path), category_name)
            except Exception:
                errors += 1
                continue

            predicted = prediction["result"]

            if ground_truth == "defective" and predicted == "defective":
                tp += 1
            elif ground_truth == "normal" and predicted == "normal":
                tn += 1
            elif ground_truth == "normal" and predicted == "defective":
                fp += 1
            elif ground_truth == "defective" and predicted == "normal":
                fn += 1

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0

    return {
        "category": category_name,
        "total": total,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate defect detection accuracy")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max images per test subfolder per category (default: all)",
    )
    args = parser.parse_args()

    if not DATASET_IMAGES_DIR.exists():
        print("ERROR: dataset_images/ not found. Run load_mvtec_dataset.py first.")
        return

    categories = sorted([p for p in DATASET_IMAGES_DIR.iterdir() if p.is_dir()])
    results = []
    methods_used = set()

    for cat_dir in categories:
        test_dir = cat_dir / "test"
        if not test_dir.exists():
            continue
        if not detector.has_reference_or_model(cat_dir.name):
            print(f"  skip {cat_dir.name}: no trained model or reference profile")
            continue

        method = "trained autoencoder" if detector.has_trained_model(cat_dir.name) else "statistical baseline"
        methods_used.add(method)
        print(f"Evaluating {cat_dir.name} ({method})...")

        result = evaluate_category(cat_dir.name, test_dir, args.limit)
        result["method"] = method
        results.append(result)

    if not results:
        print("No categories evaluated.")
        return

    agg_tp = sum(r["tp"] for r in results)
    agg_tn = sum(r["tn"] for r in results)
    agg_fp = sum(r["fp"] for r in results)
    agg_fn = sum(r["fn"] for r in results)
    agg_total = agg_tp + agg_tn + agg_fp + agg_fn
    agg_accuracy = (agg_tp + agg_tn) / agg_total if agg_total else 0
    agg_precision = agg_tp / (agg_tp + agg_fp) if (agg_tp + agg_fp) else 0
    agg_recall = agg_tp / (agg_tp + agg_fn) if (agg_tp + agg_fn) else 0
    agg_f1 = (
        (2 * agg_precision * agg_recall / (agg_precision + agg_recall))
        if (agg_precision + agg_recall)
        else 0
    )

    lines = []
    lines.append("VisionInspect AI — Defect Detection Accuracy Report")
    lines.append("=" * 68)
    lines.append(
        f"{'Category':<14}{'Method':<20}{'N':>5}{'Acc':>7}{'Prec':>7}{'Recall':>8}{'F1':>7}"
    )
    lines.append("-" * 68)
    for r in results:
        lines.append(
            f"{r['category']:<14}{r['method']:<20}{r['total']:>5}"
            f"{r['accuracy']*100:>6.1f}%"
            f"{r['precision']*100:>6.1f}%"
            f"{r['recall']*100:>7.1f}%"
            f"{r['f1']*100:>6.1f}%"
        )
    lines.append("-" * 68)
    lines.append(
        f"{'OVERALL':<14}{'':<20}{agg_total:>5}"
        f"{agg_accuracy*100:>6.1f}%"
        f"{agg_precision*100:>6.1f}%"
        f"{agg_recall*100:>7.1f}%"
        f"{agg_f1*100:>6.1f}%"
    )
    lines.append("")
    lines.append("Confusion matrix (overall):")
    lines.append(f"  True Positive  (correctly flagged defective): {agg_tp}")
    lines.append(f"  True Negative  (correctly passed normal):     {agg_tn}")
    lines.append(f"  False Positive (normal wrongly flagged):      {agg_fp}")
    lines.append(f"  False Negative (defect missed):               {agg_fn}")
    lines.append("")
    lines.append(f"Detection method(s) used in this run: {', '.join(sorted(methods_used))}")
    lines.append(
        "Note: defect TYPE labels for dataset images come directly from the "
        "dataset's folder structure, not from a trained classifier, so type "
        "classification accuracy is not reported here — only detection "
        "accuracy (normal vs defective)."
    )

    report = "\n".join(lines)
    print("\n" + report)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / "detection_accuracy_report.txt"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nSaved report to {out_path}")


if __name__ == "__main__":
    main()
