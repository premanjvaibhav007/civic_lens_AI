# CivicLens AI — Security Architecture & Threat Model

This document outlines the security controls, authentication mechanisms, authorization matrix, threat model, and vulnerability reporting procedures for the CivicLens AI platform.

---

## 1. Authentication & Session Security

1. **Password Storage**: Passwords are encrypted with `bcrypt` using cryptographic salting (cost factor $\ge 12$).
2. **JSON Web Tokens (JWT)**:
   - **Access Token**: Short-lived (15 minutes), signed using `HS256` / `RS256` with strong secret entropy.
   - **Refresh Token**: Stored with HTTP-only cookies / secure Android encrypted SharedPreferences, expiring in 7 days.
3. **Role-Based Access Control (RBAC)**:
   - `CITIZEN`: Can submit complaints, view own drafts/complaints, upvote public complaints in their jurisdiction, verify resolutions.
   - `OFFICER`: Can view assigned department queues, triage complaints, assign field crews, upload resolution proof.
   - `SUPER_ADMIN`: Can configure SLA rules, manage jurisdictions, departments, view global audit trails and analytics.

---

## 2. API & Network Security

1. **CORS & Origin Isolation**: Configured with strict origin whitelists, disallowing wildcard origins in production environments.
2. **Security Headers**:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: SAMEORIGIN` / `DENY`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `Content-Security-Policy: default-src 'self'`
3. **Input Sanitization & Injection Prevention**:
   - Pydantic v2 data validation on all HTTP request bodies.
   - Async SQLAlchemy 2.0 parameterized queries eliminate SQL injection vulnerabilities.

---

## 3. Media Ingestion & File Storage Defense

1. **MIME Type & Magic Number Verification**: Validates file headers (`image/jpeg`, `image/png`, `image/webp`) rather than trusting user-provided file extensions.
2. **Size Limits**: Enforces a strict 10MB maximum file size ceiling per image.
3. **EXIF Stripping**: Automated removal of all metadata tags (GPS, camera serials, personal identifiers) via Pillow before saving to disk or object storage.
4. **Isolated Pathing**: File storage paths are generated using UUIDv4 filenames, preventing directory traversal attacks (`../`).

---

## 4. Audit Logging & State Machine Enforcement

1. **Finite State Machine**: Complaint state transitions (`SUBMITTED` $\to$ `AI_TRIAGED` $\to$ `ASSIGNED` $\to$ `IN_PROGRESS` $\to$ `RESOLVED` $\to$ `CLOSED`) are mathematically validated in `ComplaintService`. Illegal state transitions throw HTTP 400 bad request errors.
2. **Tamper-Evident Audit Trails**: Every status change, assignment, priority adjustment, and citizen verification is recorded in the `audit_logs` database table with timestamp, actor ID, and IP address.

---

## 5. Vulnerability Disclosure Policy
If you discover a security vulnerability in CivicLens AI, please disclose it responsibly:
- **Email**: `security@civiclens.ai`
- **PGP Fingerprint**: `2B4F 88C1 0E92 771A E3D9 4981 C7B2 91A0`
- Do not publicly disclose vulnerabilities before a patch has been validated and deployed.
