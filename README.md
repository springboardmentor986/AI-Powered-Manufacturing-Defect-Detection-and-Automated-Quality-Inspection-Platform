# VisionInspect AI: Manufacturing Defect Detection & Quality Inspection Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org)
[![Vite](https://img.shields.io/badge/Vite-5+-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)
[![MVTec AD](https://img.shields.io/badge/MVTec_AD-15_Categories-00C5E8?style=flat)](https://www.mvtec.com/company/research/datasets/mvtec-ad)

**VisionInspect AI** is an AI-powered industrial quality control platform developed according to the project specifications. It enables automated manufacturing defect inspection, severity scoring, quality decision generation, and MVTec Anomaly Detection (AD) dataset exploration.

---

## 🌟 Milestone 1 Implementation (Week 1 & 2)

- **Project Initialization & Architecture**: Scalable, modular structure with FastAPI backend, React (Vite) frontend, SQLAlchemy ORM, and SQLite/PostgreSQL support.
- **Authentication & Role-Based Access Control (RBAC)**: JWT-based security with 3 distinct personas:
  - **Quality Engineer**: Image acquisition, sample inspection, manual overrides.
  - **Factory Supervisor**: Batch inspections, deletion, operational compliance.
  - **Production Manager**: High-level manufacturing analytics and security audit trails.
- **MVTec AD Dataset Integration**: Full support for all 15 industrial categories (`bottle`, `cable`, `capsule`, `carpet`, `grid`, `hazelnut`, `leather`, `metal_nut`, `pill`, `screw`, `tile`, `toothbrush`, `transistor`, `wood`, `zipper`).
- **Image Ingestion & Preprocessing**:
  - Single & drag-and-drop batch upload workflows.
  - Format, dimensions, and file integrity validation.
  - SHA-256 hash calculation, color space analysis, and thumbnail generation.
- **Live Camera / Conveyor Belt Simulator**: Simulated high-speed industrial optical scanner with laser reticle and streaming defect ingestion.
- **Executive Dashboard**: Real-time KPI statistics, compliance pass rate, defect rate, category breakdowns, and recent inspection streams.
- **Severity Assessment Framework**: Weighted formula as per Section 5 specification:
  $$\text{Severity} = (\text{Size} \times 30\%) + (\text{Location} \times 25\%) + (\text{Defect Type} \times 25\%) + (\text{Confidence} \times 20\%)$$

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- **Node.js 18+** & **npm**

### 2. Backend Setup
```bash
# Navigate to project root
cd "c:\Users\Dell\Desktop\infosys project"

# Install backend dependencies
pip install -r backend/requirements.txt

# Seed initial database with users, MVTec AD categories, and sample inspections
python backend/seed_data.py

# Start FastAPI backend server (Runs on http://127.0.0.1:8000)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive Swagger API docs available at: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install frontend dependencies
npm install

# Start Vite dev server (Runs on http://localhost:5173)
npm run dev
```

Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## 🔑 Demo Login Personas

| Role | Email / Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Quality Engineer** | `engineer@visioninspect.ai` | `password123` | Uploads, live camera, sample inspection, decision overrides |
| **Factory Supervisor** | `supervisor@visioninspect.ai` | `password123` | Batch ingestion, inspection deletion, security audit logs |
| **Production Manager** | `manager@visioninspect.ai` | `password123` | Plant-wide KPI analysis, quality trends, audit trails |

> 💡 *Tip: You can instantly switch personas with 1 click using the role badge in the top-right navbar.*

---

## 📁 Project Structure

```text
infosys project/
├── backend/
│   ├── app/
│   │   ├── config.py             # Settings, paths, JWT keys
│   │   ├── database.py           # SQLAlchemy engine & session maker
│   │   ├── main.py               # FastAPI entry point & CORS
│   │   ├── models/               # ORM Models (User, Inspection, Batch, Audit)
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── services/             # Auth, Image, and Dataset business logic
│   │   ├── routers/              # API endpoints (/auth, /inspections, /dataset, /dashboard, /audit)
│   │   └── utils/                # Dependencies & audit logger
│   ├── data/
│   │   ├── uploads/              # Uploaded product images
│   │   ├── thumbnails/           # Generated thumbnails
│   │   └── mvtec_ad/             # 15 category folders (train/test/ground_truth)
│   ├── seed_data.py              # Initial DB and MVTec AD seeder
│   └── test_verification.py      # Automated system verification test suite
│
├── frontend/
│   ├── src/
│   │   ├── api/client.js         # Axios client & API methods
│   │   ├── context/AuthContext.js# Auth state & RBAC provider
│   │   ├── components/           # Navbar, Sidebar, StatCard, InspectionTable, UploadModal, etc.
│   │   ├── pages/                # Dashboard, Inspections, Dataset, Simulator, AuditLogs
│   │   └── App.jsx               # Main application router & shell
│   ├── tailwind.config.js        # Industrial dark theme styling
│   └── vite.config.js            # Proxy configuration
│
└── docs/
    ├── architecture.md           # High-level architecture & pipeline diagrams
    └── database_schema.md        # Database dictionary & ERD diagrams
```

---

## 🧪 Verification & Automated Testing

Run the end-to-end verification script:
```bash
python backend/test_verification.py
```
This tests all 8 critical subsystems:
1. Backend health check endpoint
2. Quality Engineer authentication & JWT token generation
3. Role-Based Access Control (RBAC) role switching
4. KPI statistics calculation
5. MVTec AD 15-category explorer
6. Direct MVTec AD ingestion into live inspection queue
7. Filtered inspection querying
8. Frontend dev server availability
