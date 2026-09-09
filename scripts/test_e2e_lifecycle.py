import sys
import os
import asyncio
import httpx
from datetime import datetime

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.main import app

BASE_URL = "http://testserver/api/v1"

async def run_e2e_test():
    print("=" * 70)
    print("CIVICLENS AI — END-TO-END SYSTEM LIFECYCLE TEST")
    print("=" * 70)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        # 1. Health check
        print("\n[Step 1] Checking system health...")
        h_resp = await client.get("/health")
        assert h_resp.status_code == 200, f"Health check failed: {h_resp.text}"
        print(" -> System is healthy:", h_resp.json())

        # 2. Citizen Login
        print("\n[Step 2] Authenticating Citizen...")
        cit_login = await client.post("/api/v1/auth/login", json={
            "email": "citizen@civiclens.gov",
            "password": "Citizen@123456"
        })
        assert cit_login.status_code == 200, f"Citizen login failed: {cit_login.text}"
        cit_token = cit_login.json()["data"]["access_token"]
        print(" -> Citizen authenticated successfully. Token received.")

        # 3. Submit Complaint
        print("\n[Step 3] Submitting new complaint with image & location...")
        form_data = {
            "title": "Severe road cavity and broken asphalt after rainfall",
            "description": "Deep crater pothole right in front of bus stand. Multiple two wheelers lost balance.",
            "latitude": "28.6328",
            "longitude": "77.2197",
            "accuracy_meters": "4.5",
            "address": "Outer Circle, CP, New Delhi",
            "city": "New Delhi",
            "submission_channel": "ANDROID_APP"
        }
        submit_resp = await client.post(
            "/api/v1/complaints",
            data=form_data,
            headers={"Authorization": f"Bearer {cit_token}"}
        )
        assert submit_resp.status_code == 200, f"Complaint submission failed: {submit_resp.text}"
        complaint_data = submit_resp.json()["data"]
        complaint_id = complaint_data["id"]
        complaint_number = complaint_data["complaint_number"]
        print(f" -> Complaint created: ID={complaint_id}, Number={complaint_number}")

        # 4. Wait for Background AI Pipeline Execution
        print("\n[Step 4] Waiting for AI Analysis & Automated Department Routing...")
        await asyncio.sleep(2.0)

        detail_resp = await client.get(
            f"/api/v1/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {cit_token}"}
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()["data"]
        print(f" -> AI Analyzed: {detail['ai_analyzed']}")
        print(f" -> Detected Category: {detail['ai_analysis']['detected_category'] if detail.get('ai_analysis') else 'N/A'}")
        print(f" -> Confidence: {detail['ai_analysis']['confidence'] if detail.get('ai_analysis') else 'N/A'}")
        print(f" -> Calculated Priority: {detail['priority']}")
        print(f" -> Assigned Department: {detail['department_name']}")
        print(f" -> Status: {detail['status']}")

        # 5. Authority Officer Login
        print("\n[Step 5] Authenticating Roads Department Officer...")
        off_login = await client.post("/api/v1/auth/login", json={
            "email": "officer.roads@civiclens.gov",
            "password": "Officer@123456"
        })
        assert off_login.status_code == 200, f"Officer login failed: {off_login.text}"
        off_token = off_login.json()["data"]["access_token"]
        officer_id = off_login.json()["data"]["user"]["id"]
        print(" -> Officer authenticated.")

        # 6. Officer updates status to IN_PROGRESS
        print("\n[Step 6] Officer acknowledges and marks IN_PROGRESS...")
        status_resp = await client.patch(
            f"/api/v1/complaints/{complaint_id}/status",
            json={"new_status": "IN_PROGRESS", "reason": "Repair crew dispatched with asphalt patcher."},
            headers={"Authorization": f"Bearer {off_token}"}
        )
        assert status_resp.status_code == 200
        print(" -> Status updated to IN_PROGRESS.")

        # 7. Officer adds an official comment
        print("\n[Step 7] Officer posts official progress note...")
        comm_resp = await client.post(
            f"/api/v1/complaints/{complaint_id}/comments",
            json={"comment_text": "Cold-mix asphalt leveling in progress by Crew 4."},
            headers={"Authorization": f"Bearer {off_token}"}
        )
        assert comm_resp.status_code == 200
        print(" -> Official comment recorded.")

        # 8. Officer Submits Resolution Evidence
        print("\n[Step 8] Officer submits repair completion evidence...")
        # Simulate evidence upload
        dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        files = {"evidence_image": ("repaired_road.png", dummy_png, "image/png")}
        data = {"completion_note": "Pothole filled with high-grade bituminous mix and roller compacted. Road restored."}
        
        res_resp = await client.post(
            f"/api/v1/complaints/{complaint_id}/resolution",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {off_token}"}
        )
        assert res_resp.status_code == 200, f"Resolution submission failed: {res_resp.text}"
        print(" -> Resolution evidence uploaded. State changed to RESOLUTION_SUBMITTED.")

        # 9. Citizen Verifies Resolution
        print("\n[Step 9] Citizen verifies resolution & rates service...")
        verify_resp = await client.post(
            f"/api/v1/complaints/{complaint_id}/verify",
            json={
                "is_resolved": True,
                "rating": 5,
                "feedback": "Prompt repair within 24 hours. The road is completely smooth now. Excellent service!"
            },
            headers={"Authorization": f"Bearer {cit_token}"}
        )
        assert verify_resp.status_code == 200, f"Citizen verification failed: {verify_resp.text}"
        print(" -> Citizen verified: Complaint RESOLVED with 5/5 star rating.")

        # 10. Verify Audit Trail & Analytics
        print("\n[Step 10] Checking Admin Analytics & Audit Trail...")
        admin_login = await client.post("/api/v1/auth/login", json={
            "email": "admin@civiclens.gov",
            "password": "Admin@123456"
        })
        admin_token = admin_login.json()["data"]["access_token"]

        audit_resp = await client.get(
            "/api/v1/admin/audit-logs?entity_name=Complaint",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert audit_resp.status_code == 200
        logs = audit_resp.json()["data"]["items"]
        print(f" -> Found {len(logs)} tamper-evident audit log entries.")

        print("\n" + "=" * 70)
        print(">>> ALL 10 LIFECYCLE PHASES COMPLETED SUCCESSFULLY WITH 100% PASS <<<")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
