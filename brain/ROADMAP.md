# VisionInspect AI — Phase & Weekly Roadmap

This roadmap governs the step-by-step implementation of VisionInspect AI. After the completion of each phase, the brain folder is updated and the changes are committed and pushed to GitHub.

---

## Phase Breakdown

### ✅ Phase 1: Milestone 1 (Weeks 1 & 2) — Project Setup & Core Inspection Framework
- [x] Project architecture & folder hierarchy.
- [x] FastAPI REST backend & React 18 frontend with Vite.
- [x] JWT Authentication & Role-Based Access Control (Engineer, Supervisor, Manager).
- [x] Real MVTec AD dataset integration from `main data` (5,354 images across 15 categories).
- [x] Image upload, validation (resolution, brightness, contrast, sharpness, SHA-256), and thumbnail generation.
- [x] Conveyor Camera Simulator with real-time continuous feed.
- [x] Inspection records database, filtering, pagination, and multi-role dashboards.
- [x] Light and Dark theme support with responsive high-contrast UI.
- [x] Verification testing suite and seed scripts.

---

### ⏳ Phase 2: Milestone 2 (Week 3) — Image Preprocessing & Feature Extraction Engine
- [ ] Multi-stage Preprocessing Pipeline (`preprocessing_service.py`):
  - [ ] Standard resizing & multi-channel normalization (Min-Max, Z-score).
  - [ ] Noise reduction filters (Bilateral Filter, Gaussian Blur, Median Filter).
  - [ ] Contrast enhancement (CLAHE - Contrast Limited Adaptive Histogram Equalization, Global Histogram Equalization).
  - [ ] Morphological Industrial ROI Extraction (Otsu adaptive thresholding, bounding contour isolation).
  - [ ] Defect data augmentation (geometric rotations, illumination variations, synthetic defect injects).
- [ ] Multi-Scale Feature Extraction Engine (`feature_service.py`):
  - [ ] GLCM Texture Descriptors (Contrast, Dissimilarity, Homogeneity, Energy, Correlation).
  - [ ] Edge & Gradient Features (Canny edge density, Sobel gradient magnitudes).
  - [ ] Color / Intensity Histogram & Statistical Moments (Mean, Variance, Skewness, Kurtosis).
  - [ ] Deep Convolutional / Dense Feature Embeddings.
- [ ] Interactive Preprocessing & Feature Studio in Frontend UI:
  - [ ] Live before/after image filter comparison.
  - [ ] ROI bounding viewer & filter parameter tuning slider.
  - [ ] Interactive histogram & feature radar charts.
- [ ] Phase 2 Brain Update & Git Commit/Push.

---

### ⏳ Phase 3: Milestone 3 (Week 4) — Defect Detection & Localization Engine
- [ ] Multi-category anomaly scoring & patch-level difference analysis.
- [ ] Defect localization with bounding boxes & heatmap overlays.
- [ ] Anomaly confidence probability estimation.
- [ ] End-to-end integration into the inspection pipeline.
- [ ] Phase 3 Brain Update & Git Commit/Push.

---

### ⏳ Phase 4: Milestone 4 (Week 5) — Defect Classification & Weighted Severity Scoring
- [ ] Defect classification matching MVTec AD ground truth defect types.
- [ ] Official Severity Framework implementation:
  - Formula: `Severity = (Size * 30%) + (Location * 25%) + (Type * 25%) + (Confidence * 20%)`
  - Bands: Low (0-39), Medium (40-59), High (60-79), Critical (80-100).
- [ ] Risk assessment & automated defect dimension metrics.
- [ ] Phase 4 Brain Update & Git Commit/Push.

---

### ⏳ Phase 5: Milestone 5 (Week 6) — Quality Control Automation & Manufacturing Analytics
- [ ] Automated Pass/Fail rules engine with configurable tolerance thresholds.
- [ ] Production line stoppage alert & supervisor escalation triggers.
- [ ] Advanced Analytics Dashboard: Yield %, Defect Pareto analysis, category breakdown, throughput metrics.
- [ ] CSV & PDF inspection summary export.
- [ ] Phase 5 Brain Update & Git Commit/Push.

---

### ⏳ Phase 6: Milestone 6 (Weeks 7 & 8) — Testing, Optimization & Deployment
- [ ] Comprehensive automated test suite (Model accuracy, F1 score, API latency benchmark).
- [ ] Performance optimizations & caching.
- [ ] Docker & Docker Compose containerization.
- [ ] Final architecture, user manual, and presentation documentation.
- [ ] Phase 6 Brain Update & Git Commit/Push.
