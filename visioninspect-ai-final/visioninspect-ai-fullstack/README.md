# VisionInspect AI

AI-powered manufacturing defect detection and quality inspection platform — an internship project covering **Milestones 1 through 4**.

## Folder guide

| Folder | What it is |
|---|---|
| `backend/` | FastAPI + SQLAlchemy API: auth (M1), CV detection pipeline (M2), severity scoring (M3), validation suite (M4) |
| `frontend/` | Next.js + TypeScript + Tailwind UI that talks to the backend |
| `deploy/` | Docker Compose (prod), Nginx config, AWS EC2 + Azure setup scripts (M4) |
| `docs/` | Technical documentation and the validation report, with real computed numbers (M4) |
| `demo/` | `VisionInspect_AI_App.html` — the single-file, zero-install browser demo. Same CV logic, same severity formula, same "What Can Be Fixed" feature, running entirely client-side. Use this for a quick presentation with nothing to install. |

## Which one do I run?

- **For a presentation with no setup:** open `demo/VisionInspect_AI_App.html` in a browser (or Live Server in VS Code). Create your own username/password on first launch.
- **For the real full-stack version:** run the backend and frontend below.

## Running the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env            # edit JWT_SECRET for anything beyond local testing
uvicorn app.main:app --reload
```
API docs appear at `http://localhost:8000/docs` (FastAPI's built-in Swagger UI).

**Run the validation suite / tests directly (no server needed):**
```bash
cd backend
PYTHONPATH=. python validation/evaluate.py     # prints precision/recall/F1/mAP
PYTHONPATH=. python tests/test_pipeline.py     # runs unit tests, prints PASS/FAIL
```

## Running the frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
Open `http://localhost:3000`. The first account you create becomes Admin.

## Running everything with Docker

```bash
docker compose up --build
```
Backend on `:8000`, frontend on `:3000`.

## Milestone map

- **M1 — Foundation:** system architecture, database schema (`backend/app/models.py`), JWT auth with RBAC across four roles.
- **M2 — Detection:** classical OpenCV defect-detection pipeline (`backend/app/cv_pipeline.py`).
- **M3 — Severity & Analytics:** weighted severity scoring (`backend/app/severity.py`), pass/fail/review logic, analytics dashboards (`frontend/app/analytics`), and the "What Can Be Fixed" suggestions (`backend/app/fix_suggestions.py`).
- **M4 — Validation & Deployment:** validation suite with real precision/recall/F1/mAP (`backend/validation/`, `docs/VALIDATION_REPORT.md`), unit tests (`backend/tests/`), deployment configs (`deploy/`), and this documentation.

## Honest notes

- The validation numbers in `docs/VALIDATION_REPORT.md` are from a real run on synthetic, generated test images — reproducible with the command above. They are not a guarantee of accuracy on real factory photos; that's the natural next step.
- The AWS/Azure scripts in `deploy/` are syntax-checked, not run against a live cloud account.
- This backend/frontend code was written and syntax-checked in a sandbox without internet access, so `npm install` / `pip install` have not been run end-to-end here — check for the first-run hiccups any fresh clone can have.
