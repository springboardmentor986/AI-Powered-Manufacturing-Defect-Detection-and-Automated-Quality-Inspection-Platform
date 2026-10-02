import os
import csv


# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"D:\VisionInspectAI\ml"

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "classification",
    "evaluation_results"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "classification",
    "confusion_analysis.csv"
)


# ============================================================
# ALL 15 CATEGORIES
# ============================================================

categories = [
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


category_summary = []
all_confusions = []


# ============================================================
# PROCESS EACH CATEGORY
# ============================================================

for category in categories:

    matrix_file = os.path.join(
        RESULTS_DIR,
        f"{category}_confusion_matrix.csv"
    )

    if not os.path.exists(matrix_file):
        print(f"\nWARNING: File not found - {matrix_file}")
        continue

    # --------------------------------------------------------
    # READ CONFUSION MATRIX
    # --------------------------------------------------------

    with open(matrix_file, "r", newline="") as file:

        rows = list(csv.reader(file))

    if len(rows) < 2:
        print(f"\nWARNING: Empty matrix - {category}")
        continue

    # First row:
    # Actual \ Predicted, class1, class2, ...
    class_names = rows[0][1:]

    # Remaining rows:
    # actual_class, values...
    matrix = []

    for row in rows[1:]:

        values = []

        for value in row[1:]:
            values.append(int(value))

        matrix.append(values)

    # --------------------------------------------------------
    # BASIC COUNTS
    # --------------------------------------------------------

    total_images = sum(
        sum(row)
        for row in matrix
    )

    correct = 0

    for i in range(len(matrix)):

        if i < len(matrix[i]):
            correct += matrix[i][i]

    incorrect = total_images - correct

    if total_images > 0:
        accuracy = correct / total_images
    else:
        accuracy = 0

    # --------------------------------------------------------
    # PER-CLASS RECALL
    # --------------------------------------------------------

    per_class = []

    for i, class_name in enumerate(class_names):

        actual_images = sum(matrix[i])

        if actual_images > 0:
            recall = matrix[i][i] / actual_images
        else:
            recall = 0

        per_class.append({
            "class": class_name,
            "recall": recall,
            "actual_images": actual_images
        })

    # --------------------------------------------------------
    # FIND CONFUSION PAIRS
    # --------------------------------------------------------

    confusion_pairs = []

    for i in range(len(class_names)):

        for j in range(len(class_names)):

            # Ignore correct predictions
            if i == j:
                continue

            count = matrix[i][j]

            if count > 0:

                confusion_pairs.append({
                    "actual": class_names[i],
                    "predicted": class_names[j],
                    "count": count
                })

                all_confusions.append({
                    "category": category,
                    "actual_class": class_names[i],
                    "predicted_class": class_names[j],
                    "confused_images": count
                })

    confusion_pairs.sort(
        key=lambda x: x["count"],
        reverse=True
    )

    # --------------------------------------------------------
    # WORST CLASS
    # --------------------------------------------------------

    if per_class:

        worst = min(
            per_class,
            key=lambda x: x["recall"]
        )

    else:

        worst = {
            "class": "N/A",
            "recall": 0,
            "actual_images": 0
        }

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    if category == "toothbrush":

        decision = "KEEP_BASELINE"

    elif accuracy < 0.40:

        decision = "RETRAIN"

    elif accuracy < 0.60:

        decision = "REVIEW"

    else:

        decision = "KEEP_BASELINE"

    # --------------------------------------------------------
    # PRINT RESULTS
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(f"CATEGORY: {category}")
    print("=" * 70)

    print(f"Total test images : {total_images}")
    print(f"Correct           : {correct}")
    print(f"Incorrect         : {incorrect}")
    print(f"Accuracy          : {accuracy * 100:.2f}%")

    print()
    print("PER-CLASS RECALL")
    print("-" * 70)

    # Lowest recall first
    per_class_sorted = sorted(
        per_class,
        key=lambda x: x["recall"]
    )

    for item in per_class_sorted:

        print(
            f"{item['class']:25s} "
            f"Recall: {item['recall'] * 100:6.2f}% "
            f"Samples: {item['actual_images']}"
        )

    print()
    print("MOST CONFUSED CLASS PAIRS")
    print("-" * 70)

    if confusion_pairs:

        for pair in confusion_pairs[:5]:

            print(
                f"{pair['actual']} "
                f"-> "
                f"{pair['predicted']} "
                f": {pair['count']} image(s)"
            )

    else:

        print("No incorrect predictions.")

    print()
    print(
        f"Worst class : {worst['class']} "
        f"({worst['recall'] * 100:.2f}% recall)"
    )

    print(
        f"Decision    : {decision}"
    )

    # --------------------------------------------------------
    # SAVE CATEGORY SUMMARY
    # --------------------------------------------------------

    category_summary.append({
        "category": category,
        "test_images": total_images,
        "correct": correct,
        "incorrect": incorrect,
        "accuracy": round(accuracy, 4),
        "worst_class": worst["class"],
        "worst_class_recall": round(worst["recall"], 4),
        "decision": decision
    })


# ============================================================
# SAVE ALL CONFUSION PAIRS
# ============================================================

confusion_output = os.path.join(
    BASE_DIR,
    "classification",
    "confusion_analysis.csv"
)

with open(
    confusion_output,
    "w",
    newline=""
) as file:

    fieldnames = [
        "category",
        "actual_class",
        "predicted_class",
        "confused_images"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(all_confusions)


# ============================================================
# SAVE CATEGORY SUMMARY
# ============================================================

summary_output = os.path.join(
    BASE_DIR,
    "classification",
    "classifier_improvement_plan.csv"
)

with open(
    summary_output,
    "w",
    newline=""
) as file:

    fieldnames = [
        "category",
        "test_images",
        "correct",
        "incorrect",
        "accuracy",
        "worst_class",
        "worst_class_recall",
        "decision"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(category_summary)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print()
print("=" * 70)
print("CLASSIFIER IMPROVEMENT SUMMARY")
print("=" * 70)

print()

for item in category_summary:

    print(
        f"{item['category']:15s} | "
        f"Accuracy: {item['accuracy'] * 100:6.2f}% | "
        f"Worst: {item['worst_class']:20s} | "
        f"{item['decision']}"
    )


# ============================================================
# RETRAINING CANDIDATES
# ============================================================

print()
print("=" * 70)
print("RETRAINING CANDIDATES")
print("=" * 70)

retrain_found = False

for item in category_summary:

    if item["decision"] == "RETRAIN":

        retrain_found = True

        print(
            f"- {item['category']} "
            f"({item['accuracy'] * 100:.2f}% accuracy)"
        )

if not retrain_found:

    print("No category automatically selected.")


# ============================================================
# OUTPUT FILES
# ============================================================

print()
print("=" * 70)
print("FILES CREATED")
print("=" * 70)

print()
print("Confusion analysis:")
print(confusion_output)

print()
print("Improvement plan:")
print(summary_output)

print()
print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)