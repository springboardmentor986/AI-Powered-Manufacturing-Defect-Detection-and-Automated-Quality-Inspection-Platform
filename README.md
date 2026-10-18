# VisionInspect AI: AI-Powered Manufacturing Defect Detection & Quality Inspection Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org)
[![Vite](https://img.shields.io/badge/Vite-5+-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.9+-5C3EE8?style=flat&logo=opencv&logoColor=white)](https://opencv.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![MVTec AD](https://img.shields.io/badge/MVTec_AD-15_Industrial_Categories-00C5E8?style=flat)](https://www.mvtec.com/company/research/datasets/mvtec-ad)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat&logo=python&logoColor=white)](https://www.python.org)

**VisionInspect AI** is an enterprise-grade, end-to-end industrial computer vision and automated optical quality inspection platform. Engineered for modern Industry 4.0 manufacturing lines, the platform delivers sub-30ms real-time anomaly detection, multi-class defect classification, multi-tier severity grading, production batch control, financial scrap loss analytics, and tamper-evident audit trails across all 15 categories of the **MVTec Anomaly Detection (AD)** industrial benchmark.

---

## 📸 Platform Visual Showcase

### 1. Plant Quality Intelligence (Production Manager Dashboard)
Comprehensive plant-wide compliance analytics, financial scrap and rework loss metrics, ROI multiplier estimation, and live 15-category MVTec AD benchmark performance matrix.

![Production Manager Dashboard](PROJECT%20SCREENSHOTS/08_production_manager_dashboard.png)

---

### 2. Shift Operations & Batch Control (Factory Supervisor Dashboard)
Live production line batch monitoring with inline visual progress bars, pass/fail yields, and Section 5 Severity Risk Tier breakdown (`Low`, `Medium`, `High`, `Critical`).

![Factory Supervisor Dashboard](PROJECT%20SCREENSHOTS/07_factory_supervisor_dashboard.png)

---

### 3. Inspection Station & Defect Triage (Quality Engineer Dashboard)
Station KPIs, real-time Pareto (80/20) root cause distribution, live optical feed controls, and incoming inspection stream.

![Quality Engineer Dashboard](PROJECT%20SCREENSHOTS/02_quality_engineer_dashboard.png)

---

### 4. Real-Time Conveyor Belt Camera Simulator
Simulated high-speed optical scanning line with live viewfinder, reticle HUD telemetry (Exposure, ISO, Focus), stream rate regulation, and active defect injection (`⚡ Defect Focus`).

![Conveyor Belt Camera Simulator](PROJECT%20SCREENSHOTS/04_camera_simulator.png)

---

### 5. Multi-Layer Defect Inspection & Localization
Multi-layer visualization pipeline featuring original raw scans, bilateral filtered inputs, thermal-jet anomaly heatmaps, and bounding box contour overlays.

| Industrial Dark Ergonomics | Inspection Records Filter Database |
| :---: | :---: |
| ![Industrial Dark Mode](PROJECT%20SCREENSHOTS/03_industrial_dark_mode.png) | ![Inspection Records Database](PROJECT%20SCREENSHOTS/05_inspection_records_db.png) |

---

### 6. Security, Audit Trails & Role-Based Access Control (RBAC)
Cryptographically verifiable SHA-256 inspection hashing, tamper-evident audit logging of overrides and batch operations, and 1-click persona switching.

| Tamper-Evident System Audit Trail | 1-Click Role-Based Authentication Portal |
| :---: | :---: |
| ![Security Audit Trail](PROJECT%20SCREENSHOTS/09_security_audit_trails.png) | ![Authentication Portal](PROJECT%20SCREENSHOTS/01_auth_portal.png) |

---

## 🌟 Key Platform Capabilities

### 1. Advanced Computer Vision Pipeline
- **Adaptive Image Preprocessing**: Bilateral filtering for edge-preserving denoising, Contrast Limited Adaptive Histogram Equalization (CLAHE) for illumination variance normalization, and Otsu morphological ROI extraction.
- **Thermal-Jet Anomaly Heatmaps**: Multi-scale structural similarity (SSIM) difference maps combined with pixel-level Mahalanobis distance matrices rendered into high-contrast thermal false-color heatmaps.
- **Defect Localization & Bounding Boxes**: Adaptive thresholding and morphological contour filtering isolating micro-cracks, surface scratches, holes, broken components, and foreign material contamination.
- **Multi-Class Defect Prototype Classifier**: 17-dimensional invariant feature extractor (Hu Moments, Gabor wavelet texture filters, color moments, Local Binary Patterns) calibrated across all 15 categories to ensure strict zero false-pass adherence (`train_max_score * 1.06`).

### 2. Multi-Persona Operations (RBAC)
- **Quality Engineer**: Real-time conveyor feed monitoring, single and batch image acquisition, manual decision overrides, and technical inspection detail views.
- **Factory Supervisor**: Live production batch management (`BATCH-2026-LINE1-CONTAINERS`, `LINE2-HARDWARE`, `LINE3-SURFACES`), line throughput tracking, and Section 5 risk tier triage.
- **Production Manager**: Executive compliance monitoring, financial scrap/rework impact modeling, Pareto root-cause analysis, and PDF audit report generation.

### 3. Quantitative Severity Scoring Model
Evaluated dynamically using the weighted industrial standard:

$$\text{Severity Score} = (S \times 0.30) + (L \times 0.25) + (T \times 0.25) + (C \times 0.20)$$

| Factor | Weight | Evaluation Criteria |
| :--- | :---: | :--- |
| **Size Factor ($S$)** | 30% | Normalized defect area ratio ($\text{Defect Area} / \text{ROI Area} \times 100$) |
| **Location Factor ($L$)** | 25% | Critical Mid-Section (1.0), Functional Edge (0.8), Peripheral Margin (0.5) |
| **Defect Mode ($T$)** | 25% | Structural fracture / break (1.0), Hole / void (0.9), Surface scratch (0.6), Stain / print (0.4) |
| **Confidence Factor ($C$)** | 20% | Model anomaly confidence score ($0.0 - 1.0$) |

---

## 📦 MVTec AD Industrial Benchmark Coverage

VisionInspect AI includes out-of-the-box anomaly models and prototype weights for all **15 MVTec AD categories** (5,354 industrial images):

| Domain | Category | Object / Texture Type | Inspected Defect Modes | Target Threshold |
| :--- | :--- | :--- | :--- | :---: |
| **Containers** | `bottle` | Rigid Glass Object | Broken Large, Broken Small, Contamination | Strict CV ($\times 1.06$) |
| **Containers** | `capsule` | Pharmaceutical Solid | Crack, Faulty Imprint, Scratch, Squeeze | Strict CV ($\times 1.06$) |
| **Containers** | `pill` | Pharmaceutical Tablet | Crack, Faulty Imprint, Color, Contamination | Strict CV ($\times 1.06$) |
| **Personal Care**| `toothbrush` | Consumer Assembly | Defective Bristles | Strict CV ($\times 1.06$) |
| **Hardware** | `cable` | Wire Harness / Assembly| Bent Wire, Cable Swap, Missing Wire, Cut | Strict CV ($\times 1.06$) |
| **Hardware** | `metal_nut` | Fastener / Machined | Bent, Color, Flip, Scratch | Strict CV ($\times 1.06$) |
| **Hardware** | `screw` | Threaded Fastener | Manipulated Front, Scratch Head, Scratch Neck | Strict CV ($\times 1.06$) |
| **Electronics** | `transistor` | Semiconductor Component| Bent Lead, Cut Lead, Damaged Case | Strict CV ($\times 1.06$) |
| **Surfaces** | `carpet` | Woven Textile | Color, Cut, Hole, Metal Contamination | Strict CV ($\times 1.06$) |
| **Surfaces** | `grid` | Metallic Mesh | Bent, Broken, Glue, Thread | Strict CV ($\times 1.06$) |
| **Agriculture** | `hazelnut` | Organic Food Product | Crack, Cut, Hole, Print | Strict CV ($\times 1.06$) |
| **Materials** | `leather` | Natural Texture | Color, Cut, Fold, Glue, Poke | Strict CV ($\times 1.06$) |
| **Ceramics** | `tile` | Architectural Surface | Crack, Glue Strip, Gray Stroke, Oil, Rough | Strict CV ($\times 1.06$) |
| **Timber** | `wood` | Natural Wood Surface | Color, Combined, Hole, Scratch | Strict CV ($\times 1.06$) |
| **Fasteners** | `zipper` | Mechanical Closure | Broken Teeth, Fabric Border, Split Teeth | Strict CV ($\times 1.06$) |

---

## 🛠️ Technology Stack

```text
├── Computer Vision & Backend
│   ├── Python 3.10+
│   ├── FastAPI (Asynchronous High-Throughput REST API)
│   ├── OpenCV (clahe, bilateralFilter, Canny, contours)
│   ├── NumPy & SciPy (Spatial distance metrics & statistical profiling)
│   ├── SQLAlchemy & SQLite / PostgreSQL (Relational persistence)
│   ├── PyJWT & Passlib (Bcrypt token security)
│   └── ReportLab (Executive PDF audit report generation)
│
└── User Interface & Frontend
    ├── React 18.3+
    ├── Vite 5 (Sub-millisecond HMR bundling)
    ├── TailwindCSS 3.4 (Custom industrial dark/light design system)
    ├── Lucide React (Industrial iconography)
    └── Axios (REST client with automatic token interceptors)
```

---

## ⚡ Quick Start Guide

### Option A: One-Click Windows Launch (Recommended)
Double-click `start_project.bat` in the project root, or execute via terminal:
```bat
start_project.bat
```
This automatically boots:
- **Backend API**: `http://127.0.0.1:8001`
- **Frontend UI**: `http://localhost:5173`
- **Interactive Swagger Docs**: `http://127.0.0.1:8001/docs`

---

### Option B: Manual Setup

#### 1. Backend Setup
```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# Seed database with genuine MVTec AD samples across all 15 categories & batches
python seed_data.py

# Start FastAPI server on port 8001
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

#### 2. Frontend Setup
```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server on port 5173
npm run dev
```

Navigate to **[http://localhost:5173](http://localhost:5173)** in your browser.

---

### Option C: Docker Deployment
```bash
# Build and run entire multi-container stack
docker-compose up --build
```

---

## 🔑 Pre-Configured Demo Accounts

| Role | Username / Email | Password | Primary Scope |
| :--- | :--- | :--- | :--- |
| **Quality Engineer** | `engineer@visioninspect.ai` | `password123` | Real-time optical simulator, triage, sample inspection |
| **Factory Supervisor** | `supervisor@visioninspect.ai` | `password123` | Line batch management, throughput, risk tiers |
| **Production Manager** | `manager@visioninspect.ai` | `password123` | Executive compliance, financial scrap impact, audit reports |

> 💡 *Tip: You can switch personas instantly with 1 click using the role selector pill located in the header banner.*

---

## 🧪 Automated System Verification Test Suite

Run the full automated end-to-end test suite to verify Computer Vision unit tests and API integration:
```bash
python backend/test_verification.py
```

### Verified Test Matrix:
1. `[+] [1/10] Preprocessing (Bilateral filter + CLAHE + ROI isolation): OK`
2. `[+] [2/10] Image Quality Analysis & Usability Grading: OK`
3. `[+] [3/10] Thermal-Jet Anomaly Engine & Heatmap Generation: OK`
4. `[+] [4/10] Golden Reference Good Sample Validation: OK`
5. `[+] [5/10] Backend Health & Liveness Probe: OK`
6. `[+] [6/10] Quality Engineer Authentication & JWT Token Issuance: OK`
7. `[+] [7/10] Manufacturing Dashboard KPI & Yield Aggregations: OK`
8. `[+] [8/10] 15-Category MVTec AD Dataset Explorer: OK`
9. `[+] [9/10] Live Sample Ingestion & Instant Pipeline Scoring: OK`
10. `[+] [10/10] Comprehensive Image Quality Audit Report: OK`

---

## 📁 Repository Directory Structure

```text
├── backend/
│   ├── app/
│   │   ├── config.py                  # Environment paths & security settings
│   │   ├── database.py                # Database connection & session factory
│   │   ├── main.py                    # FastAPI application & middleware
│   │   ├── models/                    # ORM models (InspectionRecord, BatchInspection, User, AuditLog)
│   │   ├── schemas/                   # Pydantic schemas (DashboardKPIStats, InspectionRecordResponse)
│   │   ├── services/                  # Computer vision, anomaly training & analytics services
│   │   └── routers/                   # API routes (/auth, /inspections, /dashboard, /dataset, /audit)
│   ├── data/
│   │   ├── models/                    # Model registry & trained category prototypes
│   │   ├── uploads/                   # Processed product inspection images
│   │   └── thumbnails/                # Generated 280x280 thumbnail cache
│   ├── seed_data.py                   # Pristine MVTec AD database seeder
│   ├── test_verification.py           # Automated test suite
│   └── requirements.txt               # Python package dependencies
│
├── frontend/
│   ├── src/
│   │   ├── api/                       # Axios API client bindings
│   │   ├── context/                   # AuthContext (RBAC) & ThemeContext (Dark/Light)
│   │   ├── components/                # CameraSimulator, InspectionTable, RoleHeaderBanner, StatCard
│   │   ├── pages/                     # DashboardPage, InspectionRecordsPage, LoginPage, AuditPage
│   │   └── index.css                  # Industrial design tokens & animations
│   ├── package.json                   # Node.js dependencies
│   └── vite.config.js                 # Vite development proxy configuration
│
├── PROJECT SCREENSHOTS/               # High-resolution production UI showcase captures
├── LICENSE                            # MIT License
├── start_project.bat                  # One-click dual-server Windows launcher
└── README.md                          # Comprehensive project documentation
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for complete details.
