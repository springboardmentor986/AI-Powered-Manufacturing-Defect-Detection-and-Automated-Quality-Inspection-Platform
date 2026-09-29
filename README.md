# VisionInspect-AI

## AI-Powered Manufacturing Defect Detection & Automated Quality Inspection Platform

VisionInspect-AI is an AI-powered manufacturing quality inspection platform designed to automate visual inspection of manufactured products. The system analyzes product images, detects visual anomalies, classifies inspection results, evaluates defect severity, and provides quality-risk information through an interactive web dashboard.

---

# 🎯 Objectives

- Automate visual quality inspection using Artificial Intelligence.
- Detect manufacturing defects and visual anomalies from product images.
- Reduce manual inspection effort.
- Provide consistent AI-assisted inspection results.
- Analyze defect severity and quality risk.
- Maintain inspection history for future analysis.
- Provide an analytics dashboard for quality monitoring.

---

# 🚀 Key Features

## 🔐 Authentication & Authorization

- User registration and login
- JWT-based authentication
- Secure password hashing
- Protected APIs
- Role-based access
- Quality Engineer role
- Factory Supervisor role

## 📷 Image Inspection

- Product image upload
- Image format validation
- Image quality analysis
- Image preprocessing
- AI-based visual inspection
- Inspection status tracking

## 🤖 AI-Based Defect Detection

- Pretrained ResNet18 feature extractor
- Multi-scale feature extraction
- PatchCore-style anomaly detection
- Feature memory bank
- Anomaly score calculation
- Category-specific threshold calibration
- Normal / Defect classification

## ⚠️ Quality Assessment

- Severity score
- Severity level
- Defect type
- Quality-risk assessment
- Recommended action
- Inspection processing details

## 📊 Analytics

- Total inspections
- Normal inspections
- Defective inspections
- Inspection history
- Product category information
- AI inspection results
- Analytics dashboard

## 💾 Data Management

- MongoDB database
- User records
- Inspection records
- Inspection timestamps
- AI results and scores
- Persistent inspection history

---

# 🧠 AI Model

VisionInspect-AI uses a **PatchCore-style anomaly detection approach** with a pretrained **ResNet18** model as the feature extractor.

Instead of directly comparing raw image pixels, the system extracts meaningful visual representations from the image.

## 🔬 Feature Extraction

The system extracts intermediate representations from ResNet18.

### ResNet18 Feature Layers

- **Layer 2 → 128 channels**
- **Layer 3 → 256 channels**

These representations are combined to create a multi-scale feature representation.

```text
Input Image
     ↓
ResNet18
     ↓
Layer 2 Features ─────┐
                      ├──→ Multi-Scale Features
Layer 3 Features ─────┘
     ↓
384-Dimensional Feature Representation
     ↓
14 × 14 Feature Map
     ↓
196 Local Feature Patches
```

The extracted features represent visual information such as:

- Edges
- Textures
- Patterns
- Shapes
- Local visual structures
- Higher-level visual characteristics

## 🔍 PatchCore-Style Anomaly Detection

The extracted normal-product features are stored in a feature memory bank.

During inspection, the features of a new image are compared against the normal reference features.

### 🏦 Feature Memory Bank Creation

```text
Normal Product Images
        ↓
ResNet18 Feature Extraction
        ↓
Multi-Scale Feature Extraction
        ↓
Patch-Level Features
        ↓
Feature Memory Bank
```

### 🔎 Inspection Process

```text
Test Image
    ↓
Image Preprocessing
    ↓
ResNet18 Feature Extraction
    ↓
Patch-Level Features
    ↓
Comparison with Normal Feature Memory Bank
    ↓
Nearest-Normal Distance
    ↓
Anomaly Score
```

### ✅ Normal / Defect Decision

The anomaly score is compared with the calibrated threshold for the selected product category.

```text
              Anomaly Score
                    ↓
       Category-Specific Threshold
                    ↓
              ┌─────┴─────┐
              ↓           ↓
           NORMAL       DEFECT
```

---

# 🏭 Dataset Integration

The project integrates the **MVTec Anomaly Detection (MVTec AD)** dataset for industrial anomaly detection experiments.

The dataset provides normal and defective product images that are used for:

- Feature extraction
- Feature memory-bank creation
- Model evaluation
- Threshold calibration
- Anomaly detection experiments

Category-specific feature banks and thresholds are used because different product categories have different normal visual characteristics.

---

# 🎯 Threshold Calibration

A single threshold is not applied to every product category.

Instead, category-specific anomaly thresholds are calibrated using normal and defective samples.

This allows the system to adapt to the visual characteristics of different product categories.

## 🔢 Category-Specific Thresholds

| Category | Threshold |
|---|---:|
| Bottle       | 0.079466    |
| Cable | 0.209822 |
| Capsule | 0.123271 |
| Carpet | 0.106577 |
| Grid | 0.112386 |
| Hazelnut | 0.231549 |
| Leather | 0.101448 |
| Metal Nut | 0.181667 |
| Pill | 0.180071 |
| Screw | 0.160719 |
| Tile | 0.194956 |
| Toothbrush | 0.198892 |
| Transistor | 0.167431 |
| Wood | 0.226569 |
| Zipper | 0.120682 |

### Decision Process

```text
Test Image
    ↓
Anomaly Score
    ↓
Category-Specific Threshold
    ↓
Compare Score with Threshold
    ↓
Normal / Defect
```

---

# 📊 Quality Assessment

After AI inspection, the system performs a structured quality assessment.

The inspection result provides:

- Anomaly score
- Category threshold
- Severity score
- Severity level
- Defect type
- Quality-risk information
- Recommended action
- Processing time

## ⚠️ Severity Levels

| Severity Score | Severity Level |
|---|---|
| 80–100 | Critical |
| 60–79 | High |
| 40–59 | Medium |
| 0–39 | Low |

The quality assessment layer converts the AI anomaly result into a structured quality-inspection result.

---

# 📈 Analytics Dashboard

The system provides an analytics dashboard for monitoring inspection results.

## 📊 Dashboard Information

The dashboard displays:

- Total inspections
- Normal inspections
- Defective inspections
- Inspection history
- Product category
- AI result
- Anomaly score
- Threshold
- Severity information
- Inspection processing details

The dashboard provides a centralized view of manufacturing inspection activity.

---

# 🔄 Complete System Workflow

The complete VisionInspect-AI workflow is:

```text
                    USER LOGIN
                        │
                        ↓
                Authentication
                        │
                        ↓
                Inspection Dashboard
                        │
                        ↓
                  Image Upload
                        │
                        ↓
              Image Validation
                        │
                        ↓
            Image Quality Analysis
                        │
                        ↓
              Image Preprocessing
                        │
                        ↓
             ResNet18 Feature
                Extraction
                        │
                        ↓
            Multi-Scale Features
                        │
                        ↓
          PatchCore-Style Detection
                        │
                        ↓
              Feature Memory Bank
                        │
                        ↓
                Anomaly Score
                        │
                        ↓
         Category-Specific Threshold
                        │
                 ┌──────┴──────┐
                 ↓             ↓
               NORMAL        DEFECT
                 │             │
                 └──────┬──────┘
                        ↓
              Severity Assessment
                        │
                        ↓
             Quality Risk Analysis
                        │
                        ↓
             Recommended Action
                        │
                        ↓
              Store in MongoDB
                        │
                        ↓
              Inspection History
                        │
                        ↓
              Analytics Dashboard
```

---

# 🏗️ System Architecture

The system follows a full-stack architecture connecting the React frontend, FastAPI backend, AI model, and MongoDB database.

```text
                  ┌──────────────────────┐
                  │      React UI        │
                  │                      │
                  │ Login                │
                  │ Dashboard            │
                  │ Upload Inspection    │
                  │ Analytics            │
                  └──────────┬───────────┘
                             │
                             │ REST API
                             ↓
                  ┌──────────────────────┐
                  │      FastAPI         │
                  │      Backend         │
                  └──────────┬───────────┘
                             │
             ┌───────────────┼────────────────┐
             │               │                │
             ↓               ↓                ↓
       Authentication    AI Inspection     Analytics
             │               │                │
             │               ↓                │
             │        ResNet18 Features       │
             │               ↓                │
             │       PatchCore Detection      │
             │               ↓                │
             │       Quality Assessment       │
             │               │                │
             └───────────────┼────────────────┘
                             ↓
                  ┌──────────────────────┐
                  │       MongoDB        │
                  │                      │
                  │ Users                │
                  │ Inspections          │
                  └──────────────────────┘
```

---

# 📁 Project Structure

```text
VisionInspect-AI/
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── patchcore_model.py
│   │   │   ├── predictor.py
│   │   │   └── calibrate_threshold.py
│   │   │
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── inspection.py
│   │   │   └── analytics.py
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   └── quality_service.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   └── main.py
│   │
│   ├── calibrate_thresholds.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── Dashboard.jsx
│   │   ├── UploadInspection.jsx
│   │   ├── Analytics.jsx
│   │   ├── App.css
│   │   ├── Dashboard.css
│   │   ├── Analytics.css
│   │   └── index.css
│   │
│   ├── package.json
│   └── vite.config.js
│
├── models/
├── dataset/
├── uploads/
├── .gitignore
└── README.md
```

---

# 🛠️ Technology Stack

## Backend

- Python
- FastAPI
- Uvicorn
- MongoDB
- PyMongo
- JWT
- bcrypt

## AI & Computer Vision

- PyTorch
- Torchvision
- ResNet18
- PatchCore-style Anomaly Detection
- OpenCV
- NumPy
- Pillow
- Scikit-learn

## Frontend

- React
- Vite
- JavaScript
- CSS

## Development Tools

- Visual Studio Code
- Git
- GitHub
- PowerShell
- Swagger / OpenAPI

---

# 🗄️ Database

The project uses **MongoDB** for persistent data storage.

## Database

```text
visioninspect_ai
```

## Collections

```text
users
inspections
```

## Inspection Data

Inspection records contain information such as:

- Product category
- Inspection result
- Anomaly score
- Threshold
- Severity information
- Defect type
- Processing time
- Inspection status
- Timestamp
- User information

---

# 🔐 Authentication

The system uses JWT-based authentication and role-based access control.

## Authentication Flow

```text
User Registration
       ↓
Password Hashing
       ↓
MongoDB
       ↓
User Login
       ↓
JWT Token
       ↓
Protected APIs
       ↓
Inspection Dashboard
```

## Supported Roles

- Quality Engineer
- Factory Supervisor

---

# ⚙️ Backend Setup

## 1. Navigate to Backend

```powershell
cd backend
```

## 2. Create Virtual Environment

```powershell
python -m venv venv
```

## 3. Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

## 4. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

## 5. Configure MongoDB

Create a `.env` file inside the `backend` folder:

```env
MONGODB_URI=your_mongodb_connection_string
```

Do not commit the actual `.env` file to GitHub.

## 6. Start Backend

```powershell
python -m uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API Documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 💻 Frontend Setup

## 1. Navigate to Frontend

```powershell
cd frontend
```

## 2. Install Dependencies

```powershell
npm install
```

## 3. Start Frontend

```powershell
$env:ComSpec = "$env:WINDIR\System32\cmd.exe"
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 📌 Milestone Progress

## Milestone 1 — Project Foundation

Completed:

- Project objectives and workflow
- System architecture
- Database design
- UI workflow
- Frontend setup
- Backend setup
- Authentication
- Role-based access
- Image upload workflow
- Inspection management
- MVTec AD dataset integration

## Milestone 2 — AI Inspection

Completed:

- Image preprocessing
- Image quality analysis
- ResNet18 feature extraction
- Multi-scale feature extraction
- PatchCore-style anomaly detection
- Feature memory banks
- Anomaly score calculation
- Category-specific threshold calibration
- Normal / Defect classification
- AI integration with backend
- AI result display in dashboard

## Milestone 3 — Quality Assessment & Analytics

Completed:

- Defect categorization
- Severity assessment
- Quality-risk evaluation
- Quality assessment module
- Inspection history
- Analytics dashboard
- Inspection statistics
- AI result visualization
- Production quality reports
- Advanced trend monitoring
- Final testing and validation

---

# 🚧 Future Enhancements

- Improved anomaly detection performance
- Better defect localization
- Improved performance for weaker product categories
- Advanced defect analytics
- Production quality reports
- Trend monitoring
- Automated reporting
- End-to-end testing
- Performance optimization
- Docker containerization
- Cloud deployment

---

# 🔒 Security

Sensitive information must be stored using environment variables.

The following should never be committed:

```text
.env
Database credentials
Passwords
JWT secrets
API keys
Private configuration
```

The project `.gitignore` is configured to exclude sensitive and unnecessary local files.

---

# 📊 Example Inspection Result

## Hazelnut Inspection

| Property | Result |
|---|---|
| Product Category | Hazelnut |
| AI Result | DEFECT |
| Detection Method | PatchCore |
| AI Model | PatchCore-Style Multi-Scale ResNet18 |
| Anomaly Score | 0.344405 |
| Threshold | 0.231549 |
| Severity | Medium |
| Severity Score | 48.74 / 100 |
| Defect Type | Visual Anomaly |

## Recommended Action

> Perform additional quality inspection and verify the detected anomaly.

---

# 📍 Current Project Status

VisionInspect-AI currently provides a working local full-stack manufacturing inspection workflow covering:

```text
Authentication
      ↓
Image Upload
      ↓
Image Quality Analysis
      ↓
Image Preprocessing
      ↓
AI Feature Extraction
      ↓
PatchCore Anomaly Detection
      ↓
Normal / Defect Classification
      ↓
Severity Assessment
      ↓
Quality Assessment
      ↓
MongoDB Storage
      ↓
Inspection History
      ↓
Analytics Dashboard
```

The project is currently progressing toward final testing, production reporting, trend monitoring, and deployment.

---

# 👩‍💻 Project

**VisionInspect-AI**

**AI-Powered Manufacturing Defect Detection & Automated Quality Inspection Platform**

Built using Artificial Intelligence, Computer Vision, Deep Learning, FastAPI, React, and MongoDB.
