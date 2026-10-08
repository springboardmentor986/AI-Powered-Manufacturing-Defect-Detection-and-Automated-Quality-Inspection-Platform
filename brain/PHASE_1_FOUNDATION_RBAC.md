# Phase 1 (Weeks 1 & 2): Core Architecture, Authentication & Role-Based Access Control

### 1. Objectives & Scope
- Establish full-stack repository structure separating backend (`FastAPI`), frontend (`React/Vite`), and data layers.
- Implement secure JWT authentication with password hashing using `bcrypt`.
- Build Role-Based Access Control (RBAC) with 3 distinct operational personas:
  1. **Quality Engineer** (`quality_engineer`): Frontline inspection, camera streaming, live pass/fail triage.
  2. **Factory Supervisor** (`factory_supervisor`): Line supervision, batch uploads, anomaly review, yield statistics.
  3. **Production Manager** (`production_manager`): Plant-wide KPIs, scrap cost analysis, compliance audits.

---

### 2. Database Schema (SQLite ORM with SQLAlchemy)
- **`users` Table**: `id`, `username`, `email`, `hashed_password`, `full_name`, `role`, `department`, `is_active`, `created_at`, `last_login`.
- **`inspection_records` Table**: `id`, `batch_id`, `image_filename`, `image_path`, `thumbnail_path`, `category`, `status`, `quality_decision`, `defect_detected`, `defect_type`, `severity_score`, `severity_level`, `confidence`, `defect_size_ratio`, `defect_location`, `operator_id`, `reviewed_by`, `inspection_notes`, `created_at`.
- **`batch_inspections` Table**: `id`, `batch_name`, `description`, `category`, `total_images`, `processed_images`, `pass_count`, `fail_count`, `review_count`, `status`, `created_by`, `created_at`.
- **`system_audit_logs` Table**: `id`, `user_id`, `user_email`, `action`, `resource_type`, `resource_id`, `status`, `ip_address`, `details`, `timestamp`.

---

### 3. API Endpoints
- `POST /api/v1/auth/login`: Issue bearer JWT token with user persona claims.
- `GET /api/v1/auth/me`: Fetch authenticated user profile and roles.
- `GET /api/v1/inspections`: Filterable inspection records list (by category, decision, severity).
- `POST /api/v1/inspections/upload`: Multipart image upload with instant inspection trigger.
- `POST /api/v1/inspections/batch`: Multi-image batch acquisition.
- `GET /api/v1/dataset/categories`: List 15 MVTec AD categories with image counts.
- `GET /api/v1/dashboard/stats`: Aggregated yield, rejection rate, defect distribution, and audit KPIs.
