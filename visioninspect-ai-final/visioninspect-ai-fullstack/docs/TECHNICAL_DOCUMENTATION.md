# VisionInspect AI — Technical Documentation

AI-powered manufacturing defect detection and quality inspection platform. Internship project delivered across four milestones.

## 1. Architecture (Milestone 1)
- **Backend:** FastAPI + SQLAlchemy, SQLite by default (swap `DATABASE_URL` for Postgres in production).
- **Auth:** JWT tokens, bcrypt-hashed passwords, role-based access control across four roles — `admin`, `quality_engineer`, `factory_supervisor`, `production_manager`. The first account created becomes admin automatically.
- **Database schema:** `users`, `inspection_images`, `defect_records` (one image has many defect records).
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind CSS, calling the backend over a REST API.

## 2. CV Pipeline (Milestone 2)
Classical image processing (OpenCV), not a trained neural network — fully explainable, no training data required:
1. **Bilateral filter** — edge-preserving denoise (a median blur was tried first and erased thin 1–2px scratches).
2. **CLAHE** — local contrast boost so faint defects stand out.
3. **Sobel edge detection** — raw gradient magnitude, intentionally *not* normalized per image (normalizing caused false positives on clean surfaces).
4. **Absolute threshold** (~140) on the raw magnitude.
5. **Morphological closing** — joins broken edge fragments into solid regions.
6. **Connected-component analysis** — groups defect pixels into candidate regions.
7. **Shape classification** — solidity, extent, aspect ratio, and circularity together decide: crack, scratch, dent, or contamination.

## 3. Severity Scoring (Milestone 3)
Weighted formula: **Size 30% + Location 25% + Type 25% + Confidence 20%**.
- Size: larger defect area → higher score.
- Location: closer to the center of the part → higher score (more likely load-bearing or visible).
- Type: cracks weighted highest (structural risk), scratches lowest (usually cosmetic).
- Confidence: how certain the classifier is of the shape.

Bands: **critical ≥ 80, high ≥ 60, medium ≥ 35, else low.**
Decision: any critical defect → **fail**; any high/medium → **review**; otherwise **pass**.

The "What Can Be Fixed" feature maps each detected defect to a likely cause and a suggested corrective action (e.g. crack → weld/seal/replace), paired with a required action tied to its severity. It recommends next steps; it does not edit the image.

## 4. Validation & Deployment (Milestone 4)
- **Validation:** `backend/validation/` generates labeled synthetic test images and computes precision, recall, F1, per-class average precision, mAP, and a confusion matrix using IoU matching. See `docs/VALIDATION_REPORT.md` for a real run's numbers.
- **Testing:** `backend/tests/test_pipeline.py` — unit tests for the pipeline, severity logic, and IoU math, runnable without pytest (`python tests/test_pipeline.py`).
- **Deployment:** Docker Compose for local dev and production (with Nginx reverse proxy), plus setup scripts for AWS EC2 and Azure App Service — see `deploy/`.

## Limitations (stated honestly)
- Validation is on **synthetic** images; real-photo validation is the next step.
- Crack vs. scratch classification is the fuzziest boundary (see validation report).
- Accounts/login are a straightforward username+password scheme suited to a demo; production would add password reset, email verification, and audit logging.
- AWS/Azure deployment scripts are syntax-checked, not executed against a live cloud account.
