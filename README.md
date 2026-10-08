# VisionInspect AI

**AI-powered manufacturing defect detection and quality inspection platform.**

Detects product defects from images, classifies defect types, scores severity,
and provides manufacturing analytics — built across four milestones.

## Project Structure

```
visioninspect-ai/
    app/            → FastAPI backend
    frontend/        → Next.js frontend
    Dockerfile        → backend container
    frontend/Dockerfile → frontend container
    docker-compose.yml → full-stack orchestration
```

## Quick Start (Local)

**Backend**
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in PostgreSQL credentials
```
Create the database first: `CREATE DATABASE visioninspect;`
```bash
uvicorn app.main:app --reload
```
Visit http://localhost:8000/docs for the Swagger UI.

**Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
Visit http://localhost:3000.

**Loading the MVTec AD dataset (optional, realistic test data)**
```bash
python load_mvtec_dataset.py "path\to\extracted\mvtec_ad"
python build_references.py
python train_autoencoder.py
python update_defect_labels.py
```

## Quick Start (Docker)

```bash
docker compose up --build
```
This starts PostgreSQL, the backend (port 8000), and the frontend (port 3000)
as three containers. Tested and verified working, including on GitHub
Codespaces.

---

## Milestone 1 (Week 1 & 2) — Core Setup

- 6-table database schema: `users`, `categories`, `images`, `inspections`,
  `defects`, `inspection_results`
- JWT authentication with role-based access control — verified end-to-end
  (Inspector blocked from admin-only actions with `403`; Admin allowed
  with `200`)
- Image upload API and full frontend: login, signup, dashboard
  (upload + browse units), inspection detail page
- Full MVTec AD dataset loaded: 15 categories, 5,000+ images
- UI wireframes for all major screens

## Milestone 2 (Week 3 & 4) — Image Processing & Defect Detection

- Preprocessing pipeline (OpenCV): resize, grayscale, noise removal, CLAHE
  contrast enhancement
- Image quality report: sharpness/blur and brightness detection
- Defect detection engine (initial version): per-category statistical
  reference profile (mean/std of "good" training images), patch-based
  deviation scoring
- `/inspections/run/{image_id}` endpoint — runs detection, stores result
  in the database
- Live inspection results in the UI: Pass/Fail badge, confidence gauge

## Milestone 3 (Week 5 & 6) — Defect Classification & Manufacturing Analytics

- Defect type classification using the MVTec dataset's own ground-truth
  labels (e.g. "broken small", "contamination", "bent wire"); manually
  uploaded images fall back to a generic "anomaly" tag, since
  classifying an unseen image would require a trained classifier
- Full severity scoring formula, matching the project spec exactly:
  **Size (30%) + Location (25%) + Defect Type (25%) + Confidence (20%)**
  — size from affected-area coverage, location from distance to image
  center, type from a defect-keyword severity table, confidence from
  the detector's own score
- Severity breakdown UI (per-factor bars + total score) on the
  inspection detail page
- Manufacturing Analytics dashboard: total inspections, pass/fail rate,
  severity breakdown, top defect types, category-wise quality table,
  inspections-over-time trend chart

## Milestone 4 (Week 7 & 8) — Testing, Optimization & Deployment

**Accuracy validation**
- Built `evaluate_accuracy.py` — scores the detector against the MVTec
  test set's own ground truth (`test/good` = normal, every other
  `test/<defect>` folder = defective), independent of anything used to
  build the detector
- Initial statistical baseline: **Accuracy 40.9%, Precision 95.3%,
  Recall 20.8%, F1 34.2%** — high precision, but missed most real
  defects (confirmed a known weakness of simple patch-mean deviation:
  small localized defects get diluted, and naturally high-variance
  regions like textures suppress the anomaly signal)

**Model optimization — trained autoencoder**
- Upgraded the detector to a convolutional autoencoder (PyTorch),
  trained per category on only the "good" training images
  (`train_autoencoder.py`)
- Fixed a real architecture bug along the way: the first version had no
  actual bottleneck (16,384 input values compressed to 16,384 — i.e. no
  compression at all), so the network could reconstruct defects just as
  well as normal regions. Rebuilt with a genuine 8x compression
  bottleneck, forcing the model to learn what "normal" looks like
- Result after the fix: **Accuracy 67.8%, Precision 76.9%, Recall
  80.6%, F1 78.7%** — more than double the F1 score of the baseline

**Dashboard responsiveness & reporting**
- Pass/Fail status badges and category + status filters on the dashboard
- New pages: **Inspections** (full inspection history with filtering),
  **Reports** (category and defect-type quality reports with CSV
  export), **Settings** (account info)

**Deployment**
- Containerized backend and frontend with Docker; `docker-compose.yml`
  orchestrates the full stack (Postgres + backend + frontend)
- Verified working in GitHub Codespaces: all three containers build and
  run successfully; resolved a Postgres driver mismatch
  (`psycopg` → `psycopg2`) and a container-network MTU issue along the
  way

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, OpenCV, NumPy,
  PyTorch, JWT (python-jose), bcrypt
- **Frontend:** Next.js (React), CSS-in-JS
- **Containerization:** Docker, Docker Compose

## Known Limitations / Honest Notes

- Defect type classification for dataset images uses the dataset's own
  ground-truth labels rather than a trained classifier; this is a
  deliberate, documented simplification, not a hidden gap
- The anomaly detector is a lightweight per-category autoencoder trained
  from scratch on a few hundred images per category, not a large
  pretrained model — further accuracy gains are possible with more
  training data or a deeper architecture
- Cloud deployment (AWS/Azure) was validated locally and in GitHub
  Codespaces; a persistent public cloud deployment is a natural next
  step beyond this milestone
