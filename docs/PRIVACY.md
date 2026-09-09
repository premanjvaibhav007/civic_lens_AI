# CivicLens AI — Privacy Policy & Data Governance

**Last Updated**: September 2026  
**Effective Date**: September 2026

CivicLens AI ("we", "our", or "the Platform") is dedicated to protecting the privacy of citizens, government officers, and municipal workers who use our civic complaint management platform.

---

## 1. Information We Collect
1. **Account Information**: When creating an account, we collect your full name, email address, and encrypted authentication credentials.
2. **Civic Submissions**:
   - Photographic evidence of civic defects (e.g. road damage, open drains).
   - Text descriptions and category selections.
   - Geolocation coordinates (Latitude, Longitude) captured at the time of submission.
3. **Device & Network Information**:
   - IP address, operating system version, and client application identifier for rate limiting and fraud prevention.

---

## 2. Photographic Metadata & EXIF Stripping
CivicLens AI enforces automatic **EXIF Metadata Stripping** on all uploaded media before storage:
- Device serial numbers, camera lens models, user device identifiers, and embedded private EXIF data are purged during media ingestion (`StorageService`).
- GPS coordinates are extracted and attached exclusively to the complaint record itself.

---

## 3. How We Use Your Information
- Routing civic grievances to the correct municipal authority and department.
- Triaging issues using explainable AI models (Multimodal category estimation, severity scoring, duplicate detection).
- Sending status updates, assignment notifications, and resolution confirmations.
- Aggregated, anonymized urban infrastructure analytics for public municipal dashboards.

---

## 4. Data Sharing & Third Parties
- **Municipal Authorities**: Complaint descriptions, location coordinates, and defect photos are shared with authorized municipal officers and verified field maintenance teams.
- **No Commercial Sale**: We **never** sell, monetize, or license your personal information to third-party advertisers or data brokers.

---

## 5. Security & Retention
- All data in transit is encrypted using **TLS 1.3 / HTTPS**.
- Passwords are salted and hashed using **Bcrypt** with high work factors.
- JWT access tokens expire in 15 minutes; refresh tokens expire in 7 days.
- Inactive accounts or resolved complaint logs can be audited or purged upon citizen request.

---

## 6. Citizen Rights & Account Deletion
Under applicable privacy frameworks (GDPR, DPDP Act), citizens have the right to:
1. Request an export of all submitted grievances.
2. Rectify incorrect personal details.
3. Delete their account and associated personal data via the in-app profile menu or by emailing `privacy@civiclens.ai`.

---

## 7. Contact Us
For any privacy-related inquiries, please contact our Data Protection Officer at:
- **Email**: `privacy@civiclens.ai`
- **Address**: CivicLens AI Foundation, Urban Civic Data Labs, Metropolis.
