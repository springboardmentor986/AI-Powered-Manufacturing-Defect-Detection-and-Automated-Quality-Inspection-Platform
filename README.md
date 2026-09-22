# AI-Powered Manufacturing Defect Detection and Automated Quality Inspection Platform

**VisionInspect AI** — an AI-powered manufacturing quality inspection platform
that detects product defects from images, classifies defect types, scores
severity, and provides production analytics.

> This branch (`Parvathavarthini`) contains one student's implementation of
> the project (Milestones 1–3 complete).

## Project Structure

```
.
├── backend/    → FastAPI backend
└── frontend/   → Next.js frontend
```

## Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in your PostgreSQL credentials
```

Create the database in PostgreSQL first:
```sql
CREATE DATABASE visioninspect;
```

Run:
```bash
uvicorn app.main:app --reload
```

Visit:
- http://localhost:8000 → health check
- http://localhost:8000/docs → Swagger UI (signup/login/upload/inspect here)

## Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Visit http://localhost:3000 (redirects to `/login`).

## Loading the MVTec AD Dataset (optional, for realistic test data)

```bash
cd backend
python load_mvtec_dataset.py "path\to\extracted\mvtec_ad"
python build_references.py
python update_defect_labels.py
```

1. `load_mvtec_dataset.py` — loads all 15 MVTec AD categories (5,000+ images) into the database
2. `build_references.py` — builds the anomaly-detection reference profile per category
3. `update_defect_labels.py` — tags known-defective dataset images with their specific defect type (from the dataset's own folder labels)

## What's Implemented

### Milestone 1 (Week 1 & 2) — Core Setup
- 6-table database schema: users, categories, images, inspections, defects, inspection_results
- JWT authentication with role-based access control (Inspector vs Admin — tested end-to-end with 403/200 responses)
- Image upload API and a full frontend: login, signup, dashboard (upload + browse), inspection detail page
- Full MVTec AD dataset loaded (15 categories, 5,000+ images)
- UI wireframes for all major screens

### Milestone 2 (Week 3 & 4) — Image Processing & Defect Detection
- Image preprocessing pipeline (resize, grayscale, noise removal, CLAHE contrast enhancement) using OpenCV
- Image quality analysis (sharpness/blur, brightness)
- Defect detection engine: a per-category reference profile (mean/std of "good" training images) with patch-based deviation scoring — sensitive to small, localized defects
- `/inspections/run/{image_id}` endpoint — runs detection, stores Pass/Fail result + confidence in the database
- Live inspection results in the UI (Pass/Fail badge, confidence gauge)

### Milestone 3 (Week 5 & 6) — Defect Classification & Manufacturing Analytics
- Defect type classification using the MVTec dataset's own ground-truth defect labels (e.g. "broken small", "contamination", "bent wire") instead of a generic tag
- Full severity scoring formula, matching the project spec exactly:
  **Size (30%) + Location (25%) + Defect Type (25%) + Confidence (20%)**
- Severity breakdown UI (per-factor progress bars + total score) on the inspection detail page
- Manufacturing Analytics dashboard: total inspections, pass/fail rate, severity breakdown, top defect types, category-wise pass/fail table, inspections-over-time trend chart

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, OpenCV, NumPy, JWT (python-jose), bcrypt
- **Frontend:** Next.js (React), plain CSS-in-JS
- **Defect detection:** classical statistical anomaly detection (patch-based deviation from a per-category reference profile) — not a trained deep-learning model, chosen for the project timeline

## Next Steps (Milestone 4 — Week 7 & 8)

- Validate detection accuracy with proper metrics (precision/recall/F1)
- Docker containerization and cloud deployment
- Final documentation and presentation
