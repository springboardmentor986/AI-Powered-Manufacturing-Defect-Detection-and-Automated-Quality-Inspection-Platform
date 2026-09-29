# VisionInspect-AI

## AI-Powered Manufacturing Defect Detection & Quality Inspection System

VisionInspect-AI is an AI-powered manufacturing quality inspection platform that analyzes product images to detect visual defects and anomalies. The system performs image quality analysis, AI-based inspection, severity assessment, and quality-risk evaluation through a web-based dashboard.

---

## 🚀 Features

- 🔐 JWT-based authentication and role-based access
- 📷 Product image upload and validation
- 🖼️ Image quality analysis
- 🔍 AI-based anomaly detection using PatchCore-style approach
- 🧠 Multi-scale ResNet18 feature extraction
- 📊 Anomaly score and category-specific threshold comparison
- 🏷️ Normal / Defect classification
- ⚠️ Severity assessment and quality-risk evaluation
- 📋 Inspection history and result management
- 📈 Inspection analytics dashboard
- 💾 MongoDB-based data persistence
- ⚛️ React + Vite frontend
- 🌐 FastAPI backend
- 🧪 MVTec AD dataset integration

---

## 📁 Project Structure

```text
VisionInspect-AI/
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── database.py
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
│   │   └── *.css
│   └── package.json
│
├── models/
├── dataset/
├── uploads/
├── .gitignore
└── README.md
⚙️ Tech Stack
Backend
Python
FastAPI
MongoDB
PyMongo
JWT Authentication
bcrypt
AI / Computer Vision
PyTorch
Torchvision
ResNet18
PatchCore-style Anomaly Detection
OpenCV
NumPy
Scikit-learn
MVTec AD Dataset
Frontend
React
Vite
JavaScript
CSS
🧠 AI Inspection Workflow
Product Image
      ↓
Image Quality Analysis
      ↓
Image Preprocessing
      ↓
ResNet18 Feature Extraction
      ↓
Multi-Scale Feature Representation
      ↓
PatchCore-Style Anomaly Detection
      ↓
Anomaly Score
      ↓
Category-Specific Threshold
      ↓
Normal / Defect
      ↓
Severity & Quality Assessment
      ↓
MongoDB
      ↓
Analytics Dashboard
🔬 AI Model

The system uses a pretrained ResNet18 as the feature extractor.

Features are extracted from intermediate ResNet18 layers and combined to create a multi-scale representation.

The extracted features are compared with normal reference features using a PatchCore-style feature memory bank.

The system then calculates an anomaly score and compares it with the category-specific threshold to determine whether the image is Normal or Defective.
📊 Quality Assessment

The system provides:

Anomaly score
Severity score
Severity level
Defect type
Quality-risk information
Recommended action
Inspection processing details

Severity levels include:
 
Low
Medium
High
Critical
🗄️ Database

MongoDB is used for persistent storage.

Collections include:
users
inspections
Inspection records contain information such as:

Product category
Inspection result
Anomaly score
Threshold
Severity information
Processing time
Inspection status
Timestamp
