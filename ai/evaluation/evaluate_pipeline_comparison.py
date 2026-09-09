import csv
from pathlib import Path
import numpy as np
import pandas as pd
import torch

from ai.models.inspection_pipeline import InspectionPipeline
from ai.evaluation.segmentation_dataset import MVTecSegmentationDataset
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_comparison():
    print("Comprehensive Before vs After Pipeline Evaluation")

    # ------------------------------------------------------------
    # 1. EVALUATE NORMAL IMAGES (Before vs After Gating)
    # ------------------------------------------------------------
    print("\n[1/2] Evaluating Normal Images across 15 Categories...")

    # We evaluate normal images across categories
    categories = sorted(
        [
            d.name
            for d in (PROJECT_ROOT / "mvtec_anomaly_detection").iterdir()
            if d.is_dir()
        ]
    )

    pipeline = InspectionPipeline(
        normal_features_path=str(PROJECT_ROOT / "ai/models/normal_features_layer3.pt"),
        confidence_scores_path=str(PROJECT_ROOT / "ai/evaluation/confidence_scores.csv"),
        size_boundaries_path=str(PROJECT_ROOT / "ai/models/size_score_boundaries.csv"),
        segmentation_model_path=str(PROJECT_ROOT / "ai/models/defect_segmenter_unet.pt"),
        segmentation_threshold_path=str(PROJECT_ROOT / "ai/models/segmentation_threshold.txt"),
        anomaly_thresholds_path=str(PROJECT_ROOT / "ai/models/anomaly_thresholds.csv"),
        postprocessing_config_path=str(PROJECT_ROOT / "ai/models/segmentation_postprocessing.json"),
    )

    normal_before_records = []
    normal_after_records = []

    for cat in categories:
        good_dir = PROJECT_ROOT / "mvtec_anomaly_detection" / cat / "train" / "good"
        # Sample 5 normal images per category (75 images total across all 15 categories)
        good_imgs = sorted(good_dir.glob("*.png"))[:5]

        for img_p in good_imgs:
            # Before gating: unconstrained U-Net segmentation directly drives scores
            raw_mask = pipeline.segment_image(str(img_p))
            det_res = pipeline.anomaly_detector.predict(str(img_p))
            anom = det_res["anomaly_score"]
            conf = pipeline.confidence_scorer.calculate(cat, anom)

            loc_before = pipeline.location_scorer.calculate(raw_mask)
            area_before = (raw_mask > 0).sum() / raw_mask.size * 100.0
            size_before = pipeline.size_scorer.calculate(cat, area_before)
            dtype_score = pipeline.defect_type_scorer.calculate("cut")
            sev_before = pipeline.severity_scorer.calculate(
                size_score=size_before,
                location_score=loc_before,
                defect_type_score=dtype_score,
                confidence_score=conf,
            )
            dec_before = pipeline.severity_scorer.get_quality_decision(sev_before, is_anomalous=True)

            normal_before_records.append(
                {
                    "category": cat,
                    "file": img_p.name,
                    "anomaly_score": anom,
                    "confidence": conf,
                    "area": area_before,
                    "size": size_before,
                    "severity": sev_before,
                    "decision": dec_before,
                }
            )

            # After gating: pipeline with anomaly gate
            res_after = pipeline.predict(str(img_p), category=cat, defect_type="cut")
            normal_after_records.append(
                {
                    "category": cat,
                    "file": img_p.name,
                    "anomaly_score": res_after["anomaly_score"],
                    "confidence": res_after["confidence_score"],
                    "area": res_after["predicted_area_percent"],
                    "size": res_after["size_score"],
                    "severity": res_after["severity_score"],
                    "decision": res_after["quality_decision"],
                }
            )

    df_norm_before = pd.DataFrame(normal_before_records)
    df_norm_after = pd.DataFrame(normal_after_records)

    n_total_norm = len(df_norm_before)
    reject_before = (df_norm_before["decision"] == "Reject").sum()
    reject_after = (df_norm_after["decision"] == "Reject").sum()

    fpr_before = (reject_before / n_total_norm) * 100.0
    fpr_after = (reject_after / n_total_norm) * 100.0

    mean_area_norm_before = df_norm_before["area"].mean()
    mean_area_norm_after = df_norm_after["area"].mean()

    max_area_norm_before = df_norm_before["area"].max()
    max_area_norm_after = df_norm_after["area"].max()

    print("\n--- NORMAL IMAGES RESULTS ---")
    print(f"Total normal images evaluated    : {n_total_norm}")
    print(f"False Rejections (Before)        : {reject_before} / {n_total_norm} ({fpr_before:.1f}%)")
    print(f"False Rejections (After)         : {reject_after} / {n_total_norm} ({fpr_after:.1f}%)")
    print(f"Mean Defect Area % (Before)      : {mean_area_norm_before:.2f}% (max {max_area_norm_before:.2f}%)")
    print(f"Mean Defect Area % (After)       : {mean_area_norm_after:.2f}% (max {max_area_norm_after:.2f}%)")

    # ------------------------------------------------------------
    # 2. EVALUATE DEFECTIVE TEST IMAGES (Segmentation Metrics)
    # ------------------------------------------------------------
    print("\n[2/2] Evaluating Defective Test Images (260 samples in test.csv)...")

    test_csv = PROJECT_ROOT / "ai/evaluation/segmentation_splits/test.csv"
    with open(test_csv, "r", encoding="utf-8") as f:
        test_samples = [(r["image_path"], r["mask_path"]) for r in csv.DictReader(f)]

    dataset = MVTecSegmentationDataset(test_samples, image_size=224)
    loader = DataLoader(dataset, batch_size=8, shuffle=False)

    device = pipeline.segmentation_device
    model = pipeline.segmentation_model
    thresh = pipeline.segmentation_threshold

    def eval_segmentation(use_postproc=False):
        all_preds, all_targets = [], []
        actual_areas, pred_areas = [], []

        with torch.no_grad():
            for imgs, masks in loader:
                imgs = imgs.to(device)
                probs = torch.sigmoid(model(imgs)).cpu().numpy()[:, 0]
                masks_np = masks.numpy()[:, 0]

                for p, m in zip(probs, masks_np):
                    bin_mask = (p >= thresh).astype(np.uint8)
                    if use_postproc:
                        bin_mask = pipeline._postprocess_mask(bin_mask)

                    all_preds.append(bin_mask)
                    all_targets.append(m > 0)

                    actual_areas.append((m > 0).sum() / m.size * 100.0)
                    pred_areas.append((bin_mask > 0).sum() / bin_mask.size * 100.0)

        all_preds = np.asarray(all_preds, dtype=bool)
        all_targets = np.asarray(all_targets, dtype=bool)

        tp = np.logical_and(all_preds, all_targets).sum()
        fp = np.logical_and(all_preds, ~all_targets).sum()
        fn = np.logical_and(~all_preds, all_targets).sum()

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        iou = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0

        actual_areas = np.asarray(actual_areas, dtype=np.float64)
        pred_areas = np.asarray(pred_areas, dtype=np.float64)

        pearson = float(np.corrcoef(actual_areas, pred_areas)[0, 1])

        # Spearman
        act_order = np.argsort(actual_areas)
        prd_order = np.argsort(pred_areas)
        act_ranks = np.empty(len(actual_areas))
        prd_ranks = np.empty(len(pred_areas))
        act_ranks[act_order] = np.arange(len(actual_areas))
        prd_ranks[prd_order] = np.arange(len(pred_areas))
        spearman = float(np.corrcoef(act_ranks, prd_ranks)[0, 1])

        mae = float(np.mean(np.abs(pred_areas - actual_areas)))

        return prec, rec, f1, iou, pearson, spearman, mae

    b_prec, b_rec, b_f1, b_iou, b_p, b_s, b_mae = eval_segmentation(use_postproc=False)
    a_prec, a_rec, a_f1, a_iou, a_p, a_s, a_mae = eval_segmentation(use_postproc=True)

    print("\nDefective Images Segmentation Metrics:")
    print(f"{'Metric':<20}{'Before':>15}{'After':>15}{'Delta':>15}")
    print(f"{'Precision':<20}{b_prec:>15.4f}{a_prec:>15.4f}{a_prec - b_prec:>+15.4f}")
    print(f"{'Recall':<20}{b_rec:>15.4f}{a_rec:>15.4f}{a_rec - b_rec:>+15.4f}")
    print(f"{'F1 Score':<20}{b_f1:>15.4f}{a_f1:>15.4f}{a_f1 - b_f1:>+15.4f}")
    print(f"{'IoU':<20}{b_iou:>15.4f}{a_iou:>15.4f}{a_iou - b_iou:>+15.4f}")
    print(f"{'Area Pearson':<20}{b_p:>15.4f}{a_p:>15.4f}{a_p - b_p:>+15.4f}")
    print(f"{'Area Spearman':<20}{b_s:>15.4f}{a_s:>15.4f}{a_s - b_s:>+15.4f}")
    print(f"{'Mean Area Error %':<20}{b_mae:>15.4f}%{a_mae:>15.4f}%{a_mae - b_mae:>+15.4f}%")

    print("\nEvaluation Complete")


if __name__ == "__main__":
    run_comparison()
