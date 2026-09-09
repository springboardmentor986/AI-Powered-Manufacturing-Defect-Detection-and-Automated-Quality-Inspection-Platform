# VisionInspect AI — Manufacturing Defect Detection & Quality Inspection System

VisionInspect AI is an industrial-grade automated computer vision and quality inspection system engineered for high-throughput manufacturing lines. It performs real-time automatic product classification, sub-surface and surface anomaly detection, semantic defect segmentation, multi-factor severity scoring, and role-based quality decision automation.

---

## 1. Architectural Overview

VisionInspect AI employs a modular, defense-in-depth machine learning pipeline combining discriminative classification, deep feature-memory anomaly detection, and semantic segmentation:

```
Input Industrial Image (RGB)
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Multi-Task Deep Feature Extraction & Classification      │
│    ├─ ResNet18 Category Classifier (15 industrial classes)  │
│    ├─ Hierarchical Defect Classifier (Category-specific)    │
│    └─ ResNet18 Layer3 Memory Anomaly Detector (Cosine Sim)  │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Decision Fusion Layer                                    │
│    ├─ Category-specific Anomaly Threshold Gating            │
│    ├─ Subtype Discrepancy Reconciliation                    │
│    └─ Defect Status Resolution (NORMAL vs DEFECTIVE)        │
└─────────────────────────────────────────────────────────────┘
          │
    ┌─────┴────────────────────────┐
    ▼                              ▼
[If Confirmed NORMAL]       [If Confirmed DEFECTIVE]
    │                              │
    ├─ Zero Defect Mask            ├─ U-Net Semantic Segmentation
    ├─ Clean Image Pass            ├─ Morphological Post-Processing (Opening/Connected Comp.)
    ├─ Severity Score: 0.0         ├─ Physical Area Estimation (% surface area)
    └─ Decision: ACCEPT            ├─ Location Impact Scorer (Center vs Edge)
                                   ├─ Defect Type Criticality Scorer
                                   ├─ Confidence Scoring Engine
                                   └─ Multi-Factor Severity Scorer
                                           │
                                           ▼
                                   ┌───────────────────────────────────────────┐
                                   │ 3. Weighted Severity & Quality Decision   │
                                   │    Size: 30% | Location: 25%              │
                                   │    Defect Type: 25% | Confidence: 20%     │
                                   │    Decision: Accept / Reject              │
                                   └───────────────────────────────────────────┘
```

---

## 2. Key Features

- **Automatic Industrial Category Classification**: ResNet18 trained on 15 MVTec AD manufacturing categories with 100% classification accuracy.
- **Unsupervised Anomaly Detection**: Deep Layer3 ResNet18 embeddings matched against normal feature memory banks with category-calibrated thresholds.
- **Hierarchical Defect Classification**: Specialised classifiers distinguishing fine-grained defect subtypes (e.g., contamination, cut, hole, scratch).
- **Sub-Pixel Semantic Segmentation**: U-Net architecture producing pixel-level defect masks with morphological cleaning to eradicate background noise.
- **Standardized Multi-Factor Severity Scoring**:
  $$\text{Severity} = (0.30 \times \text{Size}) + (0.25 \times \text{Location}) + (0.25 \times \text{Defect Type}) + (0.20 \times \text{Confidence})$$
- **Industrial Quality Decision Engine**: Automated rule-based disposition (Low/Medium $\rightarrow$ Accept, High/Critical $\rightarrow$ Reject) with supervisor escalation.
- **Role-Based Access Control (RBAC)**:
  - **Quality Engineer (Role 1)**: Upload images, execute automated inspections, inspect overlays, view analytics.
  - **Factory Supervisor (Role 2)**: Access review queue, inspect AI recommendations, approve/reject dispositions, provide audited engineering notes.
- **Interactive Modern Frontend**: React + Vite dashboard displaying real-time inspection results, severity breakdown dials, and visual defect heatmaps.

---

## 3. Technology Stack

- **Backend**: FastAPI, Uvicorn, Pydantic v2, SQLAlchemy, Psycopg2
- **Database**: PostgreSQL 14+
- **Machine Learning & CV**: PyTorch, Torchvision, OpenCV (cv2), NumPy, Pandas, Scikit-Learn
- **Authentication**: JWT (JSON Web Tokens), Argon2 password hashing
- **Frontend**: React 19, Vite, Tailwind CSS, Lucide Icons

---

## 4. Repository Structure

```
VisionInspect_AI/
├── ai/
│   ├── evaluation/            # Validation scripts, regression suites, benchmarks
│   └── models/                # PyTorch architectures, scorers, pipelines, configs
│       ├── anomaly_detector.py
│       ├── category_classifier.py
│       ├── decision_fusion.py
│       ├── defect_classifier.py
│       ├── defect_segmenter.py
│       ├── defect_type_scorer.py
│       ├── inspection_pipeline.py
│       ├── location_scorer.py
│       ├── severity_scorer.py
│       └── size_scorer.py
├── backend/
│   ├── app/
│   │   ├── core/              # Global application settings
│   │   ├── database/          # SQLAlchemy engine & session lifecycle
│   │   ├── models/            # Database schema models (User, Image)
│   │   ├── routers/           # API routes (Auth, Image, Analytics)
│   │   ├── schemas/           # Pydantic request/response validation
│   │   ├── security/          # Password hashing, JWT tokens, RBAC dependencies
│   │   ├── services/          # Storage & file validation services
│   │   └── main.py            # FastAPI application entry point
│   ├── tests/                 # Integration & unit test suites
│   └── requirements.txt       # Backend dependencies
├── frontend/                  # React + Vite application
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Route views (Login, Register, Dashboard, Inspection)
│   │   └── services/          # API client integration
│   ├── package.json
│   └── vite.config.js
├── requirements.txt           # Top-level dependencies
├── .gitignore                 # Excludes weights, datasets, environments, uploads
└── README.md
```

---

## 5. Quickstart & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.11 - 3.14)
- Node.js 18+ & npm
- PostgreSQL 14+

### 1. Database Setup
Ensure PostgreSQL is running locally:
```bash
createdb visioninspect_db
```
Configure your connection string via the `DATABASE_URL` environment variable if different from default:
```bash
export DATABASE_URL="postgresql://<username>:<password>@localhost:5432/visioninspect_db"
```

### 2. Backend Setup
```bash
cd backend
python -m venv myvenv
source myvenv/bin/activate
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be accessible at: `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Access the application dashboard at: `http://localhost:5173`.

---

## 6. Model Weights & Data Management

Pre-trained model artifacts are stored in `ai/models/`:
- `segmentation_threshold.txt`: Calibrated U-Net binarization threshold.
- `segmentation_postprocessing.json`: Morphology parameters per industrial class.

> **Note:** Generated CSV evaluation and calibration artifacts are excluded from GitHub.

> **Note on Large Model Files**:
> Trained `.pt`, `.pth`, and `.pkl` artifacts are excluded from this repository because of their size. The repository contains the model architectures, inference pipeline, evaluation scripts, class mappings, and configuration. Required trained model artifacts must be available locally in `ai/models/` before running the complete inference pipeline.

---

## 7. Running Verification & Test Suites

Execute the comprehensive automated test suite:

```bash
# Run Milestone 1 & 2 integration tests
PYTHONPATH=backend:. ./backend/myvenv/bin/python -m unittest discover -s tests

# Run 15-sample multi-category regression suite
PYTHONPATH=. ./backend/myvenv/bin/python ai/evaluation/test_regression_inspection.py

# Run automatic classification verification
PYTHONPATH=. ./backend/myvenv/bin/python ai/evaluation/test_automatic_classification.py

# Run frontend linting & production build
cd frontend
npm run lint
npm run build
```

---

## 8. License

VisionInspect AI is developed for industrial manufacturing quality inspection benchmarks.
