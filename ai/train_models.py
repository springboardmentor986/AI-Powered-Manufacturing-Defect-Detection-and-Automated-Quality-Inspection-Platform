from pathlib import Path

from backend.app.services.image_processing import train_anomaly_model


# MVTec AD dataset location
BASE_DIR = Path("datasets/mvtec_ad")

# Folder where trained models will be saved
MODEL_DIR = Path("ai/models")

# Categories currently downloaded
CATEGORIES = [
    "bottle",
    "cable",
    "screw",
    "tile",
    "toothbrush",
    "wood",
]


def main():

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("VisionInspect AI")
    print("MVTec AD Model Training")
    print("=" * 40)

    for category in CATEGORIES:

        category_path = BASE_DIR / category

        model_path = (
            MODEL_DIR /
            f"{category}_anomaly_model.joblib"
        )

        print()
        print(f"Training category: {category}")

        try:

            result = train_anomaly_model(
                str(category_path),
                str(model_path)
            )

            print(
                f"Training images: "
                f"{result['training_images']}"
            )

            print(
                f"Model saved: "
                f"{result['model_path']}"
            )

        except Exception as error:

            print(
                f"ERROR in {category}: {error}"
            )

    print()
    print("Training completed.")


if __name__ == "__main__":
    main()