# VisionInspect AI: Manufacturing Defect Detection & Quality Inspection System
## System Architecture & Project Overview

### 1. Executive Summary
**VisionInspect AI** is an enterprise-grade, Industry 4.0 automated visual inspection platform. It leverages deep learning computer vision, anomaly detection, automated severity assessment, and real-time manufacturing analytics to detect, classify, and localize product anomalies across 15 standard industrial domains.

---

### 2. High-Level System Architecture Flow
```text
MVTec AD / Industrial Camera Feed / Direct Upload
                     │
                     ▼
             Image Acquisition
          (Single / Batch Upload & Camera Simulation)
                     │
                     ▼
          Image Preprocessing Pipeline
      (Resize, Bilateral Filter, CLAHE, ROI Extraction)
                     │
                     ▼
          Deep Feature Extraction & Embeddings
                     │
                     ▼
         Defect / Anomaly Detection Engine
     (Anomaly Localization, Heatmaps, Probability)
                     │
                     ▼
     Defect Classification & Severity Assessment
 [Severity = (Size×30%) + (Loc×25%) + (Type×25%) + (Conf×20%)]
                     │
                     ▼
         Automated Quality Decision
             (PASS / FAIL / REVIEW)
         ┌───────────┴───────────┐
         ▼                       ▼
Inspection Records        Quality Analytics
   & Audit Logs           & Yield Dashboards
```

---

### 3. Core Architectural Modules
1. **User & Role-Based Access Control (RBAC)**:
   - **Quality Engineer**: Live line inspection, camera triage, instant pass/fail validation.
   - **Factory Supervisor**: Batch operations, threshold configuration, yield analytics, anomaly review.
   - **Production Manager**: Executive plant yield KPIs, scrap cost analysis, compliance audits.
2. **Dataset & Storage Pipeline**:
   - Integrated with 5,354 real images across 15 MVTec AD categories (`bottle`, `cable`, `capsule`, `carpet`, `grid`, `hazelnut`, `leather`, `metal_nut`, `pill`, `screw`, `tile`, `toothbrush`, `transistor`, `wood`, `zipper`).
   - SQLite / SQLAlchemy persistence with automatic PostgreSQL scalability.
3. **Computer Vision & Anomaly Engine**:
   - Feature analysis, anomaly heatmaps, defect bounding geometry, and category-tailored decision thresholds.
4. **Severity Scoring Engine**:
   - Multi-factor mathematical scoring model: `Severity = (Size × 30%) + (Location × 25%) + (Defect Type × 25%) + (Confidence × 20%)`.
   - Classification levels: Low (0-39), Medium (40-59), High (60-79), Critical (80-100).
5. **Manufacturing Analytics & Auditing**:
   - Real-time yield monitoring, tamper-evident audit logging, and cross-category defect distribution matrix.
