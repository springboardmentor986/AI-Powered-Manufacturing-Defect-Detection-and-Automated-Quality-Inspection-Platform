# VisionInspect-AI

## AI-Powered Manufacturing Defect Detection & Automated Quality Inspection Platform

VisionInspect-AI is an AI-powered manufacturing quality inspection platform designed to automate visual inspection of manufactured products. The system analyzes product images, detects visual anomalies, classifies inspection results, evaluates defect severity, and provides quality-risk information through an interactive web dashboard.

The platform combines computer vision, deep learning, anomaly detection, image processing, authentication, database management, and analytics into an end-to-end quality inspection workflow.

---

## 🚀 Project Overview

In traditional manufacturing environments, quality inspection is often performed manually, which can be time-consuming and may lead to inconsistent inspection results.

VisionInspect-AI provides an automated image-based inspection system that helps quality engineers analyze product images and identify possible defects.

The system follows this workflow:

**Image Upload → Image Quality Analysis → Preprocessing → Feature Extraction → Anomaly Detection → Defect Classification → Severity Assessment → Quality Assessment → Database Storage → Analytics Dashboard**

---

## 🎯 Objectives

- Automate visual quality inspection using Artificial Intelligence.
- Detect manufacturing defects and visual anomalies from product images.
- Reduce manual inspection effort.
- Provide consistent AI-assisted inspection results.
- Analyze defect severity and quality risk.
- Maintain inspection history for future analysis.
- Provide an analytics dashboard for quality monitoring.
- Build a scalable foundation for future deployment.

---

## ✨ Key Features

### 🔐 Authentication & Authorization

- User registration and login
- JWT-based authentication
- Secure password hashing
- Protected APIs
- Role-based access
- Quality Engineer role
- Factory Supervisor role

### 📷 Image Inspection

- Product image upload
- Image format validation
- Image quality analysis
- Image preprocessing
- AI-based visual inspection
- Inspection status tracking

### 🤖 AI-Based Defect Detection

- Pretrained ResNet18 feature extractor
- Multi-scale feature extraction
- PatchCore-style anomaly detection
- Feature memory bank
- Anomaly score calculation
- Category-specific threshold calibration
- Normal / Defect classification

### ⚠️ Quality Assessment

- Severity score
- Severity level
- Defect type
- Quality-risk assessment
- Recommended action
- Inspection processing details

### 📊 Analytics

- Total inspections
- Normal inspections
- Defective inspections
- Inspection history
- Category-wise inspection information
- AI inspection results
- Analytics dashboard

### 💾 Data Management

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

### Feature Extraction

The system extracts intermediate representations from ResNet18:

- Layer 2 → 128 channels
- Layer 3 → 256 channels

The representations are combined to create a multi-scale feature representation.

```text
Input Image
     ↓
ResNet18
     ↓
Layer 2 Features ──┐
                   ├──→ Multi-Scale Features
Layer 3 Features ──┘
     ↓
384-Dimensional Feature Representation
     ↓
14 × 14 Feature Map
     ↓
196 Local Feature Patches
🔍 PatchCore-Style Anomaly Detection

The extracted normal-product features are stored in a feature memory bank.

During inspection, the features of a new image are compared against the normal reference features.
