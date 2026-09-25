from pathlib import Path
from ultralytics import YOLO



MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "best (2).pt"
)

model = YOLO(str(MODEL_PATH))




TEST_DIR = (
    Path(__file__).resolve().parent.parent
    / "yolo_dataset_final"
    / "images"
    / "test"
)




OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent
    / "prediction_results"
)

OUTPUT_DIR.mkdir(exist_ok=True)




image_extensions = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp"
}

images = [
    p for p in TEST_DIR.rglob("*")
    if p.suffix.lower() in image_extensions
]

print("Total images found:", len(images))




defect_images = 0
pass_images = 0

for index, image_path in enumerate(images, start=1):

    print(
        f"\n[{index}/{len(images)}] "
        f"{image_path.name}"
    )

    results = model.predict(
        source=str(image_path),
        imgsz=640,
        conf=0.25,
        verbose=False
    )

    result = results[0]

    
    if len(result.boxes) > 0:

        defect_images += 1

        print("RESULT: DEFECT")

        for box in result.boxes:

            confidence = float(box.conf[0])

            x1, y1, x2, y2 = (
                box.xyxy[0].tolist()
            )

            print(
                f"  defect: {confidence * 100:.1f}%"
            )

            print(
                f"  bbox: "
                f"({x1:.1f}, {y1:.1f}) "
                f"→ "
                f"({x2:.1f}, {y2:.1f})"
            )

    else:

        pass_images += 1

        print("RESULT: PASS")


    
    annotated = result.plot()

    output_path = (
        OUTPUT_DIR / image_path.name
    )

    from PIL import Image

    Image.fromarray(annotated).save(
        output_path
    )




print("\n" + "=" * 50)
print("PREDICTION COMPLETED")
print("=" * 50)

print("Total images :", len(images))
print("Defect images:", defect_images)
print("Pass images  :", pass_images)

print("\nResults saved to:")

print(OUTPUT_DIR)