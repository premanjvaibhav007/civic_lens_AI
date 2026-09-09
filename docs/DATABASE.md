# CivicLens AI — Relational Database Schema & Data Dictionary

The CivicLens AI database layer is built with **SQLAlchemy 2.0 Async** supporting PostgreSQL 16 (production) and SQLite (local dev).

---

## 1. Schema Entity Relationship

```
Users (Citizens, Officers, Admins)
  ├── 1:N ── Complaints (Reported by Citizen)
  ├── 1:N ── Complaints (Assigned Officer)
  ├── 1:N ── AuditLogs (Actor)
  └── 1:N ── Notifications (Recipient)

Departments
  ├── 1:N ── Users (Officers)
  ├── 1:N ── Complaints
  ├── 1:N ── Categories
  └── 1:N ── SLARules

Complaints
  ├── 1:N ── ComplaintMedia (Defect photos & thumbnails)
  ├── 1:N ── AIAnalysisLogs (Model predictions & feature telemetry)
  ├── 1:N ── DuplicateClusters (Associated duplicate reports)
  ├── 1:N ── AuditLogs (State transitions, assignments, edits)
  ├── 1:N ── CitizenVerifications (Feedback & satisfaction ratings)
  └── 1:N ── Upvotes (Community reinforcement)
```

---

## 2. Table Specifications

### 2.1 `users`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key | Unique user identifier |
| `email` | String(255) | Unique, Not Null, Index | User login email |
| `hashed_password` | String(255) | Not Null | Bcrypt hashed password |
| `full_name` | String(255) | Not Null | Full display name |
| `phone_number` | String(50) | Nullable | Contact number |
| `role` | Enum | Not Null | `CITIZEN`, `OFFICER`, `SUPER_ADMIN` |
| `department_id` | UUID | FK -> `departments.id` | Nullable for citizens |
| `is_active` | Boolean | Default True | Account state |
| `created_at` | DateTime | Default UTC Now | Registration timestamp |

### 2.2 `complaints`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key | Unique ticket ID |
| `complaint_number` | String(64) | Unique, Not Null, Index | Human-readable ID (e.g. `CIVIC-2026-00001`) |
| `title` | String(255) | Not Null | Grievance headline |
| `description` | Text | Not Null | Detailed issue description |
| `category` | String(100) | Not Null, Index | `POTHOLE`, `WATER_LEAKAGE`, etc. |
| `severity` | Enum | Default `MEDIUM` | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `priority` | Enum | Default `P3` | `P1`, `P2`, `P3`, `P4` |
| `status` | Enum | Default `SUBMITTED`, Index | `SUBMITTED`, `AI_TRIAGED`, `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`, `REJECTED`, `DUPLICATE` |
| `latitude` | Float | Not Null, Index | GPS Latitude |
| `longitude` | Float | Not Null, Index | GPS Longitude |
| `address` | Text | Nullable | Reverse-geocoded or citizen address |
| `citizen_id` | UUID | FK -> `users.id` | Submitting citizen |
| `assigned_officer_id` | UUID | FK -> `users.id` | Assigned nodal officer |
| `department_id` | UUID | FK -> `departments.id` | Assigned department |
| `sla_deadline` | DateTime | Nullable, Index | Timestamp when SLA will breach |
| `is_sla_breached` | Boolean | Default False, Index | SLA breach flag |
| `resolution_note` | Text | Nullable | Officer note upon resolution |
| `resolution_image_url` | String(512) | Nullable | Photo proof of physical repair |
| `created_at` | DateTime | Default UTC Now, Index | Submission timestamp |
| `updated_at` | DateTime | Default UTC Now | Last modification |

### 2.3 `ai_analysis_logs`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key |
| `complaint_id` | UUID | FK -> `complaints.id` |
| `model_name` | String(100) | Classifier / Estimator version |
| `predicted_category` | String(100) | Top predicted category |
| `confidence_score` | Float | Probability confidence [0.0, 1.0] |
| `predicted_severity` | Enum | Severity estimate |
| `predicted_priority` | Enum | Priority calculation |
| `feature_payload` | JSON | Stored visual & textual feature telemetry |
| `explanation_text` | Text | Human-readable explanation string |
| `created_at` | DateTime | Timestamp of inference |

### 2.4 `audit_logs`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key |
| `complaint_id` | UUID | FK -> `complaints.id` |
| `actor_id` | UUID | FK -> `users.id` |
| `action` | String(100) | e.g. `STATUS_CHANGE`, `ASSIGNMENT`, `AI_TRIAGE` |
| `old_value` | String(255) | Previous value |
| `new_value` | String(255) | Updated value |
| `notes` | Text | Operational comment |
| `created_at` | DateTime | Exact timestamp |
