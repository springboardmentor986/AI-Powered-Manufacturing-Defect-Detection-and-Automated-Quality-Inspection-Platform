# Milestone 2: Week 3 & 4 — Image Processing & Defect Detection Pipeline

## 1. Objectives & Scope
Build the end-to-end computer vision and defect detection pipeline:
- **Image Preprocessing**: Validation, resizing (512x512), noise reduction (bilateral filter), contrast enhancement (CLAHE), and Region of Interest (ROI) extraction.
- **Image Augmentation**: Rotation (±15°), horizontal/vertical flips, and brightness jitter for model training invariance.
- **Feature Extraction**: Deep CNN embeddings (ResNet backbone / PatchCore feature space), texture analysis, and edge/pattern detection.
- **Anomaly & Defect Detection**: Unsupervised/semi-supervised anomaly scoring against golden reference distributions from `train/good` sets.
- **Defect Localization & Heatmap Generation**: Pixel-level anomaly maps highlighting defective spatial regions.

---

## 2. Preprocessing & Augmentation Pipeline
1. **Dimension Normalization**: Rescales images to standard inspection dimensions while preserving aspect ratios.
2. **Edge-Preserving Filtering**: Bilateral filtering to smooth sensor noise without blurring sharp defect edges (scratches, cracks).
3. **Contrast Limited Adaptive Histogram Equalization (CLAHE)**: Elevates subtle structural flaws in dark or high-glare regions (e.g., metal_nut, cable, bottle).
4. **ROI Extraction**: Segmenting product boundaries from dark conveyor backgrounds to eliminate false edge anomalies.

---

## 3. Defect Prediction Engine Architecture
```text
Raw Image -> Preprocessing (CLAHE + Bilateral) -> Deep Feature Extraction
     -> Anomaly Map Computation -> Thresholding & Bounding Geometry
     -> Anomaly Probability Score & Heatmap Generation
```

---

## 4. Inspection Report Generation
- Every analyzed image produces:
  - **Raw Image Path** vs **Processed Image Path**.
  - **Defect Probability / Confidence Score** (0.00 – 1.00).
  - **Defect Localization Bounding Box** (`[x, y, w, h]`).
  - **Defect Type Prediction** (e.g., `crack`, `scratch`, `contamination`, `broken_large`).
