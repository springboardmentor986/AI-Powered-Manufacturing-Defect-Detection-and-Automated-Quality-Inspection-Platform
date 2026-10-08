# Phase 2 (Week 3): Image Preprocessing & Augmentation Pipeline

### 1. Preprocessing Flow
The VisionInspect AI preprocessing pipeline standardizes industrial images before feature extraction:
1. **Validation**: Check image dimensions (min 256x256), valid color space (RGB/Grayscale), and format (PNG, JPG, TIFF).
2. **Resizing & Aspect Ratio Preservation**: Standardized to `512x512` or `256x256` depending on category.
3. **Bilateral Filtering & Noise Reduction**: Preserves crisp defect edges while removing high-frequency sensor noise.
4. **Contrast Enhancement (CLAHE)**: Contrast Limited Adaptive Histogram Equalization to illuminate low-contrast surface anomalies.
5. **Region of Interest (ROI) Masking**: Automatically isolates object contours from industrial backgrounds.
6. **Augmentation**: Rotation (±15°), horizontal/vertical flips, subtle brightness adjustments for training resilience.

---

# Phase 3 (Week 4): AI/CV Defect Detection & Localization Engine

### 1. Anomaly Detection Architecture
- Utilizes deep feature embeddings extracted from pre-trained convolutional backbones (e.g., ResNet/PatchCore feature space).
- Compares test patch embeddings against normal baseline distributions established during training on `train/good` samples.
- Computes pixel-level anomaly maps (heatmaps) indicating defect localization and spatial probability.

---

# Phase 4 (Week 5): Defect Classification & Mathematical Severity Scoring

### 1. 4-Factor Severity Formulation
The platform evaluates defect severity using the mandated weighted formula:

$$\text{Severity Score} = (\text{Defect Size} \times 30\%) + (\text{Defect Location} \times 25\%) + (\text{Defect Type} \times 25\%) + (\text{Detection Confidence} \times 20\%)$$

### 2. Severity Classification Thresholds
- **Low (0 – 39)**: Minor cosmetic defect; acceptable for secondary use.
- **Medium (40 – 59)**: Moderate concern; flagged for manual review.
- **High (60 – 79)**: Significant defect; requires immediate rework/repair.
- **Critical (80 – 100)**: Catastrophic defect; automated product rejection.

---

# Phase 5 (Week 6): Quality Control Rules & Plant Analytics

### 1. Automated Decision Engine
- **PASS**: Defect severity $< 40$ and confidence $> 0.85$.
- **REVIEW**: Defect severity between $40$ and $59$, or borderline confidence ($0.60 - 0.85$).
- **FAIL**: Defect severity $\ge 60$ or critical defect type detected.

### 2. Analytics Dashboard KPIs
- **Plant Quality Yield (%)**: $\frac{\text{Passed Inspections}}{\text{Total Inspections}} \times 100$
- **Critical Scrap Rate (%)**: $\frac{\text{Critical Failures}}{\text{Total Inspections}} \times 100$
- **Cross-Category Benchmark Matrix**: Real-time pass/fail breakdown across all 15 MVTec AD domains.
- **Audit Compliance**: 100% tamper-evident event traceability for operator reviews and decisions.
