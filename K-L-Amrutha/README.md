# VisionInspect AI

VisionInspect AI is a manufacturing quality inspection demo with image acquisition, OpenCV anomaly detection, defect classification, severity scoring, quality decisions, inspection history, and production analytics.

## Milestone status

All four milestones are complete and verified for this repository. The project lifecycle is documented in [docs/architecture.md](docs/architecture.md) and covers the full production-style sequence from local inspection to deployment.

1. Milestone 1: inspection workflow foundation — React + FastAPI app, role-based authentication, image upload, batch/source metadata, SQLite persistence, and the inspection dashboard.
2. Milestone 2: data/model intelligence — MVTec AD dataset discovery, dataset audit, feature extraction, model training, and evaluation pipelines.
3. Milestone 3: analytics and operational visibility — inspection history, analytics summaries, audit trail, model health, and user management.
4. Milestone 4: deployment readiness — Dockerized backend/frontend stack, operational configuration, and production-friendly environment setup.

The active inspection and model are bottle-only. This workspace retains only the MVTec `bottle` category. MVTec images, uploaded sample copies, and generated model files are excluded from Git because of dataset licensing, size, and model portability. To run inspections from a fresh checkout, obtain the MVTec AD license, place its `bottle` category under `backend/data/mvtec_ad/bottle`, and run `python train_model.py` from `backend` to generate the local model.

## Run locally

Backend:

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\Activate.ps1
Push-Location backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, in a second terminal:

```powershell
Push-Location frontend
npm install
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/`. The API is at `http://127.0.0.1:8000/`, with interactive docs at `http://127.0.0.1:8000/docs`. Stop each local server with Ctrl+C in its terminal.

Demo accounts:

- Quality engineer: `engineer@factory.com` / `password123`
- Factory supervisor: `supervisor@factory.com` / `supervisor123`
- Administrator: `admin@factory.com` / `admin12345`

## Docker

Install and start Docker Desktop before running these commands. A `.env` file is optional for a local demo. For other use, create one from the template and replace its token secret:

```powershell
Copy-Item .env.example .env
```

Build and start the services from the repository root:

```powershell
docker compose up --build -d
docker compose ps
```

The web app is available at `http://127.0.0.1:5173/` and the API documentation at `http://127.0.0.1:8000/docs`.
Stop the containers with `docker compose down`. Stop any local servers using ports 8000 or 5173 before starting Compose. The SQLite database is stored inside the backend container without a persistent volume, so inspection history can be lost when that container is removed.

## API surface

- `POST /api/auth/login` authenticates demo roles.
- `POST /api/inspect` validates and inspects one image, with batch and source metadata.
- `GET /api/inspections` returns the inspection log.
- `GET /api/analytics` returns pass rate, defect mix, severity, and recent decisions.
- `GET /api/metrics` returns processing speed and automation metrics.
- `GET /api/model` returns the active model version, classes, feature count, and training sample counts.
- `GET /api/health` is the service health check.

The current persistence layer is SQLite for the milestone demo. PostgreSQL or MongoDB can replace it behind the same API contract for production deployment.

## Classification validation

Inspection, model training, and evaluation use the MVTec AD bottle category only. Non-bottle category folders have been removed from this workspace.

Run the reproducible evaluator from `backend`:

```powershell
python evaluate_model.py
```

For a faster smoke benchmark:

```powershell
python evaluate_model.py --limit-per-class 2
```

For the bottle-only stratified 80/20 holdout evaluation:

```powershell
python train_model.py
python evaluate_model.py --holdout
```

Audit the retained bottle dataset from `backend`:

```powershell
python dataset_audit.py
```

The bottle-only evaluator reports hierarchical good/bad accuracy, bad-product precision/recall/F1, four-class accuracy, per-class metrics, and a confusion matrix. Its results apply only to bottle images and are not a production accuracy guarantee.

## Tests

Run backend tests from the `backend` directory so the local module imports resolve:

```powershell
Push-Location backend
python -m unittest test_requirements.py
Pop-Location
```
