# VisionInspect AI - System Architecture

## 1. Overview

VisionInspect AI is an AI-assisted manufacturing defect detection
and quality inspection system.

The system follows a layered architecture consisting of:

- React frontend
- FastAPI backend
- Authentication and authorization
- MongoDB database
- Image storage
- Machine learning pipeline

## 2. Architecture Flow

User
  |
  v
React Frontend
  |
  | REST API / Axios
  v
FastAPI Backend
  |
  +--------------------+
  |                    |
  v                    v
Authentication      Inspection APIs
  |                    |
  v                    v
JWT + Roles        Image Storage
                       |
                       v
                  ML Pipeline
                       |
                       v
                 Defect Prediction
                       |
                       v
                  MongoDB Atlas

## 3. User Roles

### Quality Engineer

- Login
- Upload product images
- Create inspections
- View inspection status
- Review inspection results

### Factory Supervisor

- Login
- View inspection activity
- Monitor quality information
- Review inspection records

## 4. Technology Stack

Frontend:
- React
- Vite
- Axios
- React Router

Backend:
- Python
- FastAPI
- JWT authentication
- bcrypt password hashing

Database:
- MongoDB Atlas

Machine Learning:
- Python
- OpenCV
- NumPy
- MVTec AD dataset

Storage:
- Local uploads directory during development

## 5. Current Inspection Workflow

Login
  |
  v
Role verification
  |
  v
Dashboard
  |
  v
Upload product image
  |
  v
Image validation
  |
  v
Store image
  |
  v
Create inspection record
  |
  v
Pending AI analysis
  |
  v
Future defect prediction pipeline