# CivicLens AI — Google Play Store Release Specification

This document details the complete metadata, Data Safety Form declarations, target audience ratings, permissions justifications, and listing copy required for publishing **CivicLens AI** on the Google Play Console.

---

## 1. Store Listing Metadata

- **App Name**: CivicLens AI: Civic Grievance & Fix Tracker
- **Short Description (80 chars)**: Report potholes, lights & civic issues with AI verification and live tracking.
- **Full Description (4000 chars)**:
```text
Transform your city with CivicLens AI — the intelligent, citizen-first civic infrastructure resolution platform. 

Whether it's a hazardous pothole, an open manhole, a non-functional streetlight, or overflowing municipal waste, CivicLens AI empowers citizens to report civic defects with photographic proof, precise geotagging, and instant AI-assisted departmental triage.

KEY FEATURES:
📸 AI-Powered Smart Reporting: Snap a photo and let our on-device and cloud multimodal AI automatically classify the defect, suggest the responsible municipal department, and estimate severity.
📍 Precise Geotagging & Offline Drafts: Never lose a complaint due to weak signal. CivicLens stores drafts locally and syncs automatically via background workers once connectivity resumes.
⏱️ Live SLA Countdown & Timeline: Track your grievance in real time from submission to officer verification, on-site crew dispatch, and resolution.
🗺️ Interactive Neighborhood Map: View resolved and active civic issues in your vicinity. Upvote existing complaints to highlight recurring community hazards without creating redundant tickets.
🛡️ Official Resolution Proof: Municipal field engineers upload geotagged resolution photos before closing tickets, ensuring genuine physical repairs.
🌐 Bilingual Support: Fully localized in English and Hindi (हिन्दी) for seamless accessibility across diverse communities.

DATA PRIVACY & INTEGRITY:
CivicLens AI strips sensitive EXIF metadata from uploaded images and encrypts all communications with municipal servers. We never sell your personal data or track your location in the background.

Empower your community today with CivicLens AI.
```

- **Category**: Public Administration / Tools
- **Content Rating**: Everyone (PEGI 3 / ESRB Everyone)
- **Support Email**: support@civiclens.ai
- **Privacy Policy URL**: `https://civiclens.ai/privacy`

---

## 2. Google Play Data Safety Declarations

| Data Type | Collected / Shared | Purpose | Optional or Required |
| :--- | :--- | :--- | :--- |
| **Approximate & Precise Location** | Collected (Not shared with 3rd parties) | App functionality (attaching GPS to municipal civic complaints) | Required at time of reporting |
| **Photos and Videos** | Collected (Uploaded to municipal server) | App functionality (photographic evidence of civic infrastructure defects) | Required at time of reporting |
| **Name & Email Address** | Collected | Account management, authentication, grievance tracking updates | Required for registered users |
| **Crash Logs & Diagnostics** | Collected | Analytics & stability diagnostics | Optional |

- **Data Encryption in Transit**: Yes (HTTPS / TLS 1.3)
- **Account Deletion Mechanism**: Yes (In-app Account Deletion and data purge endpoint `/api/v1/auth/delete-account`)
- **Children's Policy**: Does not knowingly collect data from children under 13.

---

## 3. Runtime Permissions Justification

1. `android.permission.CAMERA`:
   - **Reason**: Allows citizens to take real-time photos of potholes, streetlights, and civic hazards directly within the complaint submission flow.
2. `android.permission.ACCESS_FINE_LOCATION` & `ACCESS_COARSE_LOCATION`:
   - **Reason**: Attaches exact GPS coordinates to the infrastructure complaint so municipal field maintenance crews can locate and repair the defect.
3. `android.permission.READ_MEDIA_IMAGES` / `READ_EXTERNAL_STORAGE`:
   - **Reason**: Enables citizens to select existing photo evidence of civic issues from their photo gallery.
4. `android.permission.POST_NOTIFICATIONS`:
   - **Reason**: Sends real-time notifications to citizens when the status of their grievance changes (e.g. Assigned, Crew Dispatched, Resolved).

---

## 4. Screenshot & Graphic Asset Specs

- **App Icon**: 512 x 512 px PNG (32-bit with alpha, max 1024KB).
- **Feature Graphic**: 1024 x 500 px JPG or 24-bit PNG (no alpha).
- **Phone Screenshots**: Minimum 4 screenshots (1080 x 2400 px, 18:9 or 20:9 ratio):
  1. *Screen 1*: Home Dashboard with active grievance timeline and quick report trigger.
  2. *Screen 2*: AI Smart Camera capture with real-time bounding box and category tag.
  3. *Screen 3*: Interactive Neighborhood Map with clustered civic pins.
  4. *Screen 4*: Detailed Ticket Timeline showing before/after resolution photos.
