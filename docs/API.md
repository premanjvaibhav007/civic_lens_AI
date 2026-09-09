# CivicLens AI — REST API v1 Specification

Base URL: `/api/v1`

All responses follow standard HTTP status codes and JSON payload bodies.

---

## 1. Authentication Endpoints (`/auth`)

### `POST /auth/register`
Registers a new citizen account.
- **Request Body**:
```json
{
  "email": "citizen@example.com",
  "password": "SecurePassword123!",
  "full_name": "Rajesh Kumar",
  "phone_number": "+919876543210"
}
```
- **Response `201 Created`**:
```json
{
  "id": "c1f2e3d4-...",
  "email": "citizen@example.com",
  "full_name": "Rajesh Kumar",
  "role": "CITIZEN",
  "is_active": true
}
```

### `POST /auth/login`
Authenticates a user and returns JWT bearer tokens.
- **Request Body**: `OAuth2PasswordRequestForm` or JSON `{ "email": "...", "password": "..." }`
- **Response `200 OK`**:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 900,
  "role": "CITIZEN",
  "user": { ... }
}
```

---

## 2. Complaint Endpoints (`/complaints`)

### `POST /complaints`
Submits a new civic infrastructure complaint.
- **Auth**: Required (`CITIZEN` or `SUPER_ADMIN`)
- **Request Body**:
```json
{
  "title": "Massive deep pothole on Ring Road",
  "description": "Deep asphalt crater causing traffic bottleneck and accident risk",
  "category": "POTHOLE",
  "latitude": 28.6328,
  "longitude": 77.2197,
  "address": "Ring Road Sector 14, Metropolis",
  "media_urls": ["/storage/uploads/c123.jpg"]
}
```
- **Response `201 Created`**: Returns created complaint object with assigned `complaint_number` (e.g. `CIVIC-2026-00001`), initial status `SUBMITTED`, and triggered async AI triage task.

### `GET /complaints`
Lists complaints with filtering and pagination.
- **Query Params**:
  - `page`: int (default 1)
  - `limit`: int (default 20)
  - `status`: string (e.g. `SUBMITTED`, `IN_PROGRESS`, `RESOLVED`)
  - `category`: string (e.g. `POTHOLE`, `WATER_LEAKAGE`)
  - `department_id`: UUID
  - `search`: string

### `GET /complaints/{id}`
Fetches single complaint details including audit trail, AI analysis results, and resolution images.

### `PATCH /complaints/{id}/status`
Transitions a complaint state (Officer / Admin only).
- **Request Body**:
```json
{
  "status": "IN_PROGRESS",
  "note": "Maintenance team dispatched to site with asphalt patch unit."
}
```

### `POST /complaints/{id}/resolve`
Marks a complaint as resolved with mandatory photographic proof.
- **Request Body**:
```json
{
  "resolution_note": "Pothole filled with cold asphalt mix and steam-rolled.",
  "resolution_image_url": "/storage/uploads/res_456.jpg"
}
```

### `POST /complaints/{id}/verify`
Citizen verification of the physical repair.
- **Request Body**:
```json
{
  "is_satisfied": true,
  "feedback": "Pothole has been completely leveled. Great work!"
}
```

---

## 3. Analytics Endpoints (`/analytics`)

### `GET /analytics/overview`
Returns high-level KPI dashboard metrics:
```json
{
  "total_complaints": 1284,
  "resolved_count": 1042,
  "in_progress_count": 180,
  "pending_count": 62,
  "sla_compliance_percentage": 94.8,
  "avg_resolution_hours": 18.4,
  "category_breakdown": {
    "POTHOLE": 450,
    "STREETLIGHT": 320,
    "WATER_LEAKAGE": 210,
    "GARBAGE": 304
  }
}
```

### `GET /analytics/heatmap`
Returns geo-points `[{ lat, lng, weight, category, id }]` for map heatmap layers.

---

## 4. Storage Endpoints (`/storage`)

### `POST /storage/upload`
Uploads raw image, sanitizes EXIF, creates thumbnail.
- **Form Data**: `file: UploadFile`
- **Response `200 OK`**:
```json
{
  "url": "/storage/uploads/3a8f-2810.jpg",
  "thumbnail_url": "/storage/thumbnails/3a8f-2810_thumb.jpg",
  "filename": "3a8f-2810.jpg",
  "size_bytes": 145020,
  "mime_type": "image/jpeg"
}
```
