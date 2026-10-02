# VisionInspect AI - Database Schema

## Database

MongoDB Atlas

## Collection: users

| Field | Type | Description |
|---|---|---|
| _id | ObjectId | Unique user identifier |
| name | String | User's name |
| email | String | User email |
| password_hash | String | Securely hashed password |
| role | String | User role |
| created_at | DateTime | Account creation time |

### Allowed Roles

- quality_engineer
- factory_supervisor


## Collection: inspections

| Field | Type | Description |
|---|---|---|
| _id | ObjectId | Unique inspection identifier |
| filename | String | Original uploaded filename |
| stored_filename | String | Filename used in storage |
| user_id | String | User who created inspection |
| role | String | Role of inspecting user |
| status | String | Current inspection status |
| result | Object/Null | AI inspection result |
| created_at | DateTime | Inspection creation time |

### Current Status

pending

### Future Statuses

- processing
- completed
- failed


## Relationships

users
  |
  | user_id
  v
inspections

One user can create multiple inspections.