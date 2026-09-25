# VisionInspect AI

AI-powered manufacturing quality inspection system for detecting and classifying defects in industrial products using YOLO and ResNet18.

## Project Overview

VisionInspect AI is a web-based quality inspection application designed to assist manufacturing quality engineers in identifying defective products from industrial images.

The system uses a two-stage computer vision pipeline:

1. YOLO detects the location of a defect.
2. ResNet18 classifies the detected defect type.
3. A severity scoring system evaluates the defect.
4. A quality assessment determines the recommended action.
5. Inspection results are stored in PostgreSQL.
6. React dashboards display inspection, quality, report, and analytics information.

The application allows users to upload an inspection image, process it through the FastAPI backend, run the trained YOLO model, classify detected defects using ResNet18, and generate a quality assessment.


## Features

### Authentication and Authorization

- User registration and login
- JWT-based authentication
- Password hashing using bcrypt
- Role-based access control
- Quality Engineer role
- Factory Supervisor role

### Inspection

- Industrial image upload
- YOLO-based defect detection
- Defect bounding-box detection
- YOLO confidence score
- ResNet18-based defect classification
- Classification confidence
- Inspection history
- Inspection result storage

### Severity and Quality Assessment

The system calculates defect severity using:


Severity =
(Size × 0.30)
+ (Location × 0.25)
+ (Defect Type × 0.25)
+ (Confidence × 0.20)

Severity levels:

| Score  | Severity | Recommended Action |
| ------ | -------- | ------------------ |
| 80–100 | Critical | Reject             |
| 60–79  | High     | Rework             |
| 40–59  | Medium   | Review             |
| 0–39   | Low      | Accept             |

If classification confidence is below 70%, the inspection is marked for manual review.

## Machine Learning Pipeline

Input Image
     ↓
YOLO26n
     ↓
Defect Detection
     ↓
Defect Bounding Box
     ↓
Crop Detected Region
     ↓
ResNet18
     ↓
Defect Classification
     ↓
Severity Calculation
     ↓
Quality Assessment
     ↓
PostgreSQL
     ↓
React Dashboard

## Technology Stack

### Frontend

React.js
Vite
JavaScript
Tailwind CSS
Recharts

### Backend
Python
FastAPI
SQLAlchemy
Pydantic
JWT
Passlib
bcrypt

### Database
PostgreSQL

### Machine Learning
YOLO26n
ResNet18
PyTorch
Torchvision
Ultralytics
OpenCV
NumPy
Pillow
### Dataset
MVTec AD

### Reporting
CSV export
PDF export
ReportLab

## Project Structure

```text
VisionInspectAI/
│
├── backend/
│   ├── ml/
│   │   ├── integrated_inspection.py
│   │   ├── ml_service.py
│   │   ├── severity.py
│   │   ├── test_classifier.py
│   │   ├── test_models.py
│   │   ├── test_resnet.py
│   │   └── test_yolo.py
│   │
│   ├── tests/
│   │   └── test_severity.py
│   │
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── predict_all.py
│   ├── requirements.txt
│   └── schemas.py
│
├── vite-project/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   └── pages/
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
