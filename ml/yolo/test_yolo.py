from pathlib import Path

from ultralytics import YOLO

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR
    / "runs"
    / "bottle_defect_improved"
    / "weights"
    / "best.pt"
)

DATA_YAML = BASE_DIR / "data.yaml"


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"YOLO model not found: {MODEL_PATH}")
    if not DATA_YAML.exists():
        raise FileNotFoundError(f"Dataset config not found: {DATA_YAML}")

    test_split = BASE_DIR / "dataset" / "test" / "images"
    if not test_split.exists():
        print(f"Skipping YOLO validation: no test split found at {test_split}")
        return

    print("=" * 60)
    print("Loading improved YOLO model")
    print("=" * 60)

    model = YOLO(str(MODEL_PATH))

    print("Improved YOLO model loaded successfully!")

    print("\n" + "=" * 60)
    print("Evaluating improved YOLO on TEST dataset")
    print("=" * 60)

    results = model.val(
        data=str(DATA_YAML),
        split="test",
        imgsz=640,
        batch=8
    )

    print("\n" + "=" * 60)
    print("IMPROVED YOLO TEST RESULTS")
    print("=" * 60)

    print(f"Precision    : {results.box.mp:.4f}")
    print(f"Recall       : {results.box.mr:.4f}")
    print(f"mAP@0.5      : {results.box.map50:.4f}")
    print(f"mAP@0.5:0.95 : {results.box.map:.4f}")

    print("=" * 60)


if __name__ == "__main__":
    main()