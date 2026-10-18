import sys
import os
import time
from pathlib import Path

# Ensure backend package is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
from app.services.anomaly_training_service import AnomalyTrainingService

def main():
    print("=" * 70)
    print("   VisionInspect AI — Actual MVTec AD Dataset Training Pipeline")
    print(f"   Target Dataset Path: {settings.ACTIVE_DATASET_DIR}")
    print(f"   Output Models Path:  {settings.MODELS_DIR}")
    print("=" * 70)

    if not settings.ACTIVE_DATASET_DIR.exists():
        print(f"[!] Error: Active dataset path does not exist: {settings.ACTIVE_DATASET_DIR}")
        sys.exit(1)

    print("\n[*] Initializing training across all 15 MVTec AD Categories...")
    t_start = time.time()
    results = AnomalyTrainingService.train_all_categories()

    print("\n" + "=" * 70)
    print("                       TRAINING RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'Category':<14} | {'Type':<8} | {'Train Imgs':<10} | {'Acc (%)':<8} | {'F1-Score':<8} | {'Latency':<8}")
    print("-" * 70)

    for m in results.get("models", []):
        cat = m["category"]
        c_type = m["category_type"]
        tr_imgs = m["train_samples"]
        acc = f"{m.get('accuracy', 0.0) * 100:.1f}%"
        f1 = f"{m.get('f1_score', 0.0):.3f}"
        lat = f"{m.get('mean_inference_latency_ms', 0.0):.1f}ms"
        print(f"{cat:<14} | {c_type:<8} | {tr_imgs:<10} | {acc:<8} | {f1:<8} | {lat:<8}")

    print("-" * 70)
    print(f"[+] Total Categories Trained: {results['categories_trained']}/15")
    print(f"[+] Total Duration:           {results['total_duration_seconds']:.2f} seconds")
    print(f"[+] Registry Saved:           {AnomalyTrainingService.REGISTRY_FILE}")
    print("=" * 70)

if __name__ == "__main__":
    main()
