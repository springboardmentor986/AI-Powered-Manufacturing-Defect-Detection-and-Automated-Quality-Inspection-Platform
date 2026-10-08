# VisionInspect AI — Brain & Knowledge Base

## 1. Executive Summary
**VisionInspect AI** is an industrial-grade AI-powered Manufacturing Defect Detection & Quality Inspection platform developed according to the Infosys Springboard Industry 4.0 specifications.

The platform provides end-to-end automated visual inspection, defect detection, multi-class defect classification, weighted severity assessment (Low, Medium, High, Critical), automated Pass/Fail quality decisions, line stoppage alerts, and manufacturing analytics.

---

## 2. Dataset Integration & Validation
- **Dataset Path**: `C:\Users\Dell\Desktop\infosys project\main data`
- **Dataset Standard**: Full MVTec Anomaly Detection (MVTec AD) benchmark dataset
- **Categories (15/15 Active)**:
  - **Texture Categories (5)**: `carpet`, `grid`, `leather`, `tile`, `wood`
  - **Object Categories (10)**: `bottle`, `cable`, `capsule`, `hazelnut`, `metal_nut`, `pill`, `screw`, `toothbrush`, `transistor`, `zipper`
- **Total Dataset Inventory**:
  - **Total Images**: 5,354 images
  - **Train (Good / Defect-Free)**: 3,629 images
  - **Test (Good)**: 467 images
  - **Test (Defects)**: 1,258 images across 70+ industrial defect types
  - **Pixel-level Ground Truth Masks**: Available for all 15 categories

---

## 3. High-Level Architecture Flow

```text
[ Industrial Camera / Upload / MVTec AD ]
                   │
                   ▼
       [ Image Acquisition & Metadata ]
                   │
                   ▼
     [ Preprocessing & ROI Extraction ]
                   │
                   ▼
      [ Multi-Scale Feature Extraction ]
                   │
                   ▼
       [ AI Defect / Anomaly Engine ]
                   │
                   ▼
  [ Defect Classification & Severity Scoring ]
                   │
                   ▼
     [ Automated Pass/Fail Quality Decision ]
         │                    │
         ▼                    ▼
[ Inspection Logs DB ]  [ Manufacturing Analytics Dashboard ]
```

---

## 4. Multi-Role RBAC Specification
The system implements strict Role-Based Access Control (RBAC) with 3 specialized dashboards:
1. **Quality Engineer (`engineer@factory.com`)**:
   - Camera Simulator & Real-time acquisition
   - Manual single & batch image upload
   - Visual inspection inspection modal with zoom and defect overlay
   - Preprocessing inspection & feature explorer
2. **Factory Supervisor (`supervisor@factory.com`)**:
   - Production line monitoring & real-time shift metrics
   - Defect severity distribution (Low/Medium/High/Critical)
   - Quality alert acknowledgments & line stoppage overrides
   - Daily inspection throughput & yield monitoring
3. **Production Manager (`manager@factory.com`)**:
   - Plant-wide Yield Rate (%) and First-Pass-Yield (FPY)
   - Defect Pareto distribution across all 15 categories
   - Root-cause analysis & production downtime risk reports
   - CSV/JSON inspection report exports & audit trail review

---

## 5. Technology Stack
- **Backend**: FastAPI (Python 3.12), SQLAlchemy, Pydantic v2, Passlib/Bcrypt, PyJWT, Pillow, NumPy, OpenCV, Scikit-Learn
- **Frontend**: React 18, Vite, Tailwind CSS v4, Lucide React, Recharts, Custom Theme Engine (Dark / Light)
- **Database**: SQLite (local development) / PostgreSQL (production-ready ORM)
- **AI / Vision**: OpenCV, Deep Feature Embeddings, Morphological ROI, GLCM Texture Descriptors, Patch-based Anomaly Scorers
