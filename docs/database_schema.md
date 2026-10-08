# VisionInspect AI — Database Schema & Data Dictionary

## 1. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    User ||--o{ InspectionRecord : performs
    User ||--o{ BatchInspection : creates
    User ||--o{ SystemAuditLog : triggers
    BatchInspection ||--o{ InspectionRecord : groups

    User {
        int id PK
        string username UK
        string email UK
        string hashed_password
        string full_name
        string role
        string department
        boolean is_active
        datetime created_at
        datetime last_login
    }

    BatchInspection {
        string id PK
        string batch_name
        string description
        string category
        int total_images
        int processed_images
        int pass_count
        int fail_count
        int review_count
        string status
        int created_by FK
        datetime created_at
        datetime updated_at
    }

    InspectionRecord {
        string id PK
        string batch_id FK
        string image_filename
        string image_path
        string thumbnail_path
        string original_filename
        int file_size_bytes
        int image_width
        int image_height
        int color_channels
        string file_format
        string image_hash
        string category
        string split
        string defect_type
        string status
        string quality_decision
        float confidence_score
        float severity_score
        string severity_level
        json inspection_metadata
        text notes
        int uploaded_by FK
        datetime created_at
        datetime updated_at
    }

    SystemAuditLog {
        string id PK
        int user_id FK
        string user_email
        string action
        string resource_type
        string resource_id
        string status
        string ip_address
        json details
        datetime timestamp
    }
```

## 2. Table Specifications

### `users`
Stores user identities, hashed credentials, department assignments, and RBAC roles (`quality_engineer`, `factory_supervisor`, `production_manager`, `admin`).

### `batch_inspections`
Aggregates manufacturing line batches with total unit counts, pass/fail totals, and line status.

### `inspection_records`
Core inspection entity storing raw and thumbnail image paths, image dimensions, SHA-256 integrity hash, MVTec AD category, defect classification, severity scoring (0–100), pass/fail decision, and operator notes.

### `system_audit_logs`
Compliance audit trail logging user authentication, image ingestion, batch creation, and manual decision overrides.
