import os
import csv
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
sys.path.insert(0, BASE_DIR)

from inference.inspection_pipeline import inspect_image
CATEGORIES = [
    "bottle",
    "cable",
    "capsule",
    "carpet",
    "grid",
    "hazelnut",
    "leather",
    "metal_nut",
    "pill",
    "screw",
    "tile",
    "toothbrush",
    "transistor",
    "wood",
    "zipper"
]

OUTPUT_FILE = os.path.join(BASE_DIR, "evaluation", "full_pipeline_results.csv")


def main():

    results = []

    total = 0
    correct = 0

    for category in CATEGORIES:

        test_dir = os.path.join(DATASET_DIR, category, "test")

        if not os.path.exists(test_dir):
            print(f"\n[SKIP] {category} - test folder not found")
            continue

        print("\n" + "=" * 70)
        print(f"TESTING CATEGORY: {category.upper()}")
        print("=" * 70)

        defect_folders = [
            x for x in os.listdir(test_dir)
            if os.path.isdir(os.path.join(test_dir, x))
        ]

        for defect_folder in sorted(defect_folders):

            folder_path = os.path.join(test_dir, defect_folder)

            expected = "GOOD" if defect_folder == "good" else "DEFECT"

            image_files = [
                x for x in os.listdir(folder_path)
                if x.lower().endswith((".png", ".jpg", ".jpeg"))
            ]

            for image_file in sorted(image_files):

                image_path = os.path.join(folder_path, image_file)

                total += 1

                try:
                    result = inspect_image(image_path, category)

                    predicted = result.get("status", "ERROR")

                    is_correct = predicted == expected

                    if is_correct:
                        correct += 1

                    results.append({
                        "category": category,
                        "expected": expected,
                        "defect_folder": defect_folder,
                        "image": image_file,
                        "predicted": predicted,
                        "correct": is_correct,
                        "autoencoder_decision": result.get(
                            "autoencoder_decision", ""
                        ),
                        "reconstruction_error": result.get(
                            "reconstruction_error", ""
                        ),
                        "threshold": result.get("threshold", ""),
                        "defect_count": len(result.get("defects", [])),
                        "defect_type": result.get(
                            "classification", {}
                        ).get("defect_type", ""),
                        "classification_confidence": result.get(
                            "classification", {}
                        ).get("confidence", ""),
                        "severity": result.get(
                            "quality_assessment", {}
                        ).get("severity", {}).get("level", ""),
                        "severity_score": result.get(
                            "quality_assessment", {}
                        ).get("severity", {}).get("score", ""),
                        "decision": result.get(
                            "quality_assessment", {}
                        ).get("quality_decision", "")
                    })

                    print(
                        f"{category:12} | "
                        f"{defect_folder:25} | "
                        f"{image_file:12} | "
                        f"Expected={expected:6} | "
                        f"Predicted={predicted:6} | "
                        f"{'OK' if is_correct else 'WRONG'}"
                    )

                except Exception as e:

                    print(
                        f"{category:12} | "
                        f"{defect_folder:25} | "
                        f"{image_file:12} | "
                        f"ERROR: {e}"
                    )

                    results.append({
                        "category": category,
                        "expected": expected,
                        "defect_folder": defect_folder,
                        "image": image_file,
                        "predicted": "ERROR",
                        "correct": False,
                        "autoencoder_decision": "",
                        "reconstruction_error": "",
                        "threshold": "",
                        "defect_count": "",
                        "defect_type": "",
                        "classification_confidence": "",
                        "severity": "",
                        "severity_score": "",
                        "decision": ""
                    })

    # Save CSV
    fieldnames = [
        "category",
        "expected",
        "defect_folder",
        "image",
        "predicted",
        "correct",
        "autoencoder_decision",
        "reconstruction_error",
        "threshold",
        "defect_count",
        "defect_type",
        "classification_confidence",
        "severity",
        "severity_score",
        "decision"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(results)

    accuracy = (correct / total * 100) if total else 0

    print("\n")
    print("=" * 70)
    print("FULL PIPELINE TEST COMPLETED")
    print("=" * 70)

    print(f"Total images tested : {total}")
    print(f"Correct predictions : {correct}")
    print(f"Wrong predictions   : {total - correct}")
    print(f"Accuracy            : {accuracy:.2f}%")

    print("\nResults saved to:")
    print(OUTPUT_FILE)

    # Category summary
    print("\nCATEGORY SUMMARY")
    print("-" * 70)

    for category in CATEGORIES:

        category_results = [
            r for r in results
            if r["category"] == category
        ]

        if not category_results:
            continue

        category_correct = sum(
            1 for r in category_results if r["correct"]
        )

        category_total = len(category_results)

        category_accuracy = (
            category_correct / category_total * 100
        )

        print(
            f"{category:12} : "
            f"{category_correct}/{category_total} "
            f"({category_accuracy:.2f}%)"
        )


if __name__ == "__main__":
    main()