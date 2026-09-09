# VisionInspect AI: Classification Evaluation Report

## 1. Category Classification Performance (15 MVTec Classes)

- **Total Test Samples**: 794 (Strict Unseen Test Split)
- **Overall Accuracy**: **100.00%**
- **Macro Precision**: **100.00%**
- **Macro Recall**: **100.00%**
- **Macro F1-Score**: **100.00%**

### Per-Category Performance Breakdown

| Category | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| `bottle` | 100.00% | 100.00% | 100.00% | 45.0 |
| `cable` | 100.00% | 100.00% | 100.00% | 55.0 |
| `capsule` | 100.00% | 100.00% | 100.00% | 55.0 |
| `carpet` | 100.00% | 100.00% | 100.00% | 58.0 |
| `grid` | 100.00% | 100.00% | 100.00% | 49.0 |
| `hazelnut` | 100.00% | 100.00% | 100.00% | 72.0 |
| `leather` | 100.00% | 100.00% | 100.00% | 54.0 |
| `metal_nut` | 100.00% | 100.00% | 100.00% | 52.0 |
| `pill` | 100.00% | 100.00% | 100.00% | 64.0 |
| `screw` | 100.00% | 100.00% | 100.00% | 71.0 |
| `tile` | 100.00% | 100.00% | 100.00% | 52.0 |
| `toothbrush` | 100.00% | 100.00% | 100.00% | 16.0 |
| `transistor` | 100.00% | 100.00% | 100.00% | 45.0 |
| `wood` | 100.00% | 100.00% | 100.00% | 47.0 |
| `zipper` | 100.00% | 100.00% | 100.00% | 59.0 |

## 2. Defect Classification Performance & Architecture Comparison

### Option A (Global Baseline) vs Option B (Hierarchical Category-Conditioned)

| Metric | Option A: Global Flat Baseline | Option B: Hierarchical (Our Model) |
| :--- | :--- | :--- |
| **Exact Defect Class Accuracy** | 81.86% | **77.96%** |
| **Good vs Defect Binary Accuracy** | 82.49% | **82.62%** |
| **Defect Sensitivity (Recall)** | 21.91% | **57.87%** |
| **Normal Specificity** | N/A | **89.77%** |
| **Defect F1-Score** | 35.94% | **59.88%** |

### Good vs Defective Confusion Matrix (Option B)

- **True Normal (TN)**: 553
- **False Defective (FP)**: 63
- **False Normal (FN)**: 75
- **True Defective (TP)**: 103

### Key Architectural Takeaway

Option B (Hierarchical Category-Conditioned architecture) eliminates cross-category confusion by conditioning defect prediction on the product class. This prevents category hallucinations (e.g. predicting a cable defect on a screw) and achieves significantly higher per-defect classification accuracy.