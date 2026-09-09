import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import engine, Base, AsyncSessionLocal
from backend.app.models.entities import (
    User, Citizen, Department, Jurisdiction, Officer, Category,
    RoutingRule, SLARule, Complaint, ComplaintLocation, ComplaintImage,
    ComplaintAIAnalysis, ComplaintStatusHistory, ResolutionEvidence,
    DuplicateCandidate, UserRole, ComplaintStatus, SeverityLevel,
    DuplicateCandidate, UserRole, ComplaintStatus, SeverityLevel,
    PriorityLevel, AIStatus, DuplicateStatus,
    CivicIncident, InfrastructureAsset, IncidentReport, IncidentStatusHistory,
    IncidentPrediction
)
from backend.app.core.security import get_password_hash

async def init_db():
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        res = await session.execute(select(User).where(User.email == "admin@civiclens.gov"))
        if res.scalars().first():
            print("Database already initialized with seed data.")
            return

        print("Seeding database with production initial data...")

        # 1. Admin User
        admin_user = User(
            email="admin@civiclens.gov",
            hashed_password=get_password_hash("Admin@123456"),
            full_name="Chief Municipal Administrator",
            phone="+919876543210",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        session.add(admin_user)

        # 2. Departments
        depts_data = [
            ("Municipal Roads Department", "ROADS", "Maintains city arterial roads, bridges, and pothole repairs", "roads@civiclens.gov", "+911122334401"),
            ("Electrical & Public Lighting Department", "ELECTRICAL", "Oversees streetlights, transformers, and public fixtures", "lighting@civiclens.gov", "+911122334402"),
            ("Solid Waste & Sanitation Department", "SANITATION", "Garbage collection, illegal dumping, and public cleanliness", "sanitation@civiclens.gov", "+911122334403"),
            ("Water Supply & Sewerage Board", "WATER", "Drinking water pipeline maintenance and sewer overflows", "water@civiclens.gov", "+911122334404"),
            ("Stormwater & Drainage Department", "DRAINAGE", "Rainwater drains, nalah maintenance, and flood prevention", "drainage@civiclens.gov", "+911122334405"),
            ("Traffic & Road Safety Cell", "TRAFFIC", "Signboards, speed breakers, pedestrian signals, and road markings", "traffic@civiclens.gov", "+911122334406"),
            ("Civil Infrastructure & Footpath Division", "FOOTPATH", "Pedestrian walkways, paver blocks, and public parks", "civil@civiclens.gov", "+911122334407"),
            ("Underground Drainage & Safety Department", "MANHOLE", "Manhole covers, chamber repairs, and safety barricades", "safety@civiclens.gov", "+911122334408")
        ]
        dept_map = {}
        for name, code, desc, email, phone in depts_data:
            d = Department(name=name, code=code, description=desc, contact_email=email, contact_phone=phone, is_active=True)
            session.add(d)
            dept_map[code] = d

        # 3. Jurisdictions
        jur_data = [
            ("New Delhi", "Central Zone", "Ward 101 - Connaught Place"),
            ("New Delhi", "North Zone", "Ward 102 - Civil Lines"),
            ("New Delhi", "South Zone", "Ward 103 - Hauz Khas"),
            ("New Delhi", "East Zone", "Ward 104 - Mayur Vihar"),
            ("New Delhi", "West Zone", "Ward 105 - Rajouri Garden")
        ]
        jur_list = []
        for city, zone, ward in jur_data:
            j = Jurisdiction(city=city, zone=zone, ward=ward, is_active=True)
            session.add(j)
            jur_list.append(j)

        await session.flush()

        # 4. Officer Accounts
        officers_data = [
            ("officer.roads@civiclens.gov", "Officer Rajesh Kumar", "ROADS", "ENG-RD-101", "Senior Executive Engineer"),
            ("officer.sanitation@civiclens.gov", "Officer Priya Sharma", "SANITATION", "ENG-SN-204", "Sanitary Inspector"),
            ("officer.electrical@civiclens.gov", "Officer Amit Verma", "ELECTRICAL", "ENG-EL-308", "Assistant Electrical Engineer")
        ]
        officer_map = {}
        for email, name, dept_code, badge, desig in officers_data:
            u = User(
                email=email,
                hashed_password=get_password_hash("Officer@123456"),
                full_name=name,
                phone=f"+91980000{badge[-4:]}",
                role=UserRole.OFFICER,
                is_active=True,
                is_verified=True
            )
            session.add(u)
            await session.flush()
            
            off = Officer(
                user_id=u.id,
                department_id=dept_map[dept_code].id,
                jurisdiction_id=jur_list[0].id,
                badge_number=badge,
                designation=desig,
                is_active=True
            )
            session.add(off)
            officer_map[dept_code] = off

        # 5. Demo Citizen Accounts
        citizen_user = User(
            email="citizen@civiclens.gov",
            hashed_password=get_password_hash("Citizen@123456"),
            full_name="Aarav Mehta",
            phone="+919812345678",
            role=UserRole.CITIZEN,
            is_active=True,
            is_verified=True
        )
        session.add(citizen_user)
        await session.flush()

        citizen = Citizen(
            user_id=citizen_user.id,
            default_city="New Delhi",
            total_reports=5,
            verified_reports=3,
            badge_score=85
        )
        session.add(citizen)

        # 6. Categories
        categories_data = [
            ("Pothole", "POTHOLE", "Hazardous holes and craters in road asphalt", "ROADS", PriorityLevel.P2, SeverityLevel.HIGH, "alert-triangle"),
            ("Damaged Road Surface", "DAMAGED_ROAD", "Eroded or cracked road surface causing traffic disruption", "ROADS", PriorityLevel.P3, SeverityLevel.MEDIUM, "activity"),
            ("Broken Streetlight", "STREETLIGHT", "Non-functional or flickering public street lamps", "ELECTRICAL", PriorityLevel.P3, SeverityLevel.MEDIUM, "sun"),
            ("Overflowing Garbage", "GARBAGE", "Uncollected garbage bins causing sanitation hazards", "SANITATION", PriorityLevel.P2, SeverityLevel.HIGH, "trash-2"),
            ("Illegal Dumping", "ILLEGAL_DUMPING", "Unauthorized dumping of debris or industrial waste", "SANITATION", PriorityLevel.P3, SeverityLevel.MEDIUM, "truck"),
            ("Clogged Drainage", "DRAINAGE", "Blocked storm drains causing water accumulation", "DRAINAGE", PriorityLevel.P2, SeverityLevel.HIGH, "droplet"),
            ("Drinking Water Leakage", "WATER_LEAKAGE", "Pipeline burst or potable water wastage", "WATER", PriorityLevel.P1, SeverityLevel.CRITICAL, "droplets"),
            ("Damaged Traffic Signboard", "DAMAGED_SIGN", "Broken, bent or missing road signs", "TRAFFIC", PriorityLevel.P4, SeverityLevel.LOW, "help-circle"),
            ("Damaged Footpath", "FOOTPATH", "Broken sidewalk tiles or pedestrian curb hazards", "FOOTPATH", PriorityLevel.P3, SeverityLevel.MEDIUM, "compass"),
            ("Open Manhole Cover", "OPEN_MANHOLE", "Missing or broken drain cover creating life-safety risk", "MANHOLE", PriorityLevel.P1, SeverityLevel.CRITICAL, "shield-alert")
        ]
        cat_map = {}
        for name, code, desc, dept_code, def_prio, def_sev, icon in categories_data:
            cat = Category(
                name=name,
                code=code,
                description=desc,
                default_department_id=dept_map[dept_code].id,
                default_priority=def_prio,
                default_severity=def_sev,
                icon_name=icon,
                is_active=True
            )
            session.add(cat)
            cat_map[code] = cat

        # 7. Routing Rules
        for code, cat in cat_map.items():
            rule = RoutingRule(
                name=f"Auto-route {cat.name} to {cat.default_department_id}",
                category_id=cat.id,
                target_department_id=cat.default_department_id,
                is_active=True
            )
            session.add(rule)

        # 8. SLA Rules
        for prio, res_hrs, esc_hrs in [
            (PriorityLevel.P1, 24, 36),
            (PriorityLevel.P2, 48, 72),
            (PriorityLevel.P3, 96, 120),
            (PriorityLevel.P4, 168, 240)
        ]:
            sla = SLARule(
                priority=prio,
                resolution_time_hours=res_hrs,
                escalation_time_hours=esc_hrs,
                is_active=True
            )
            session.add(sla)

        await session.flush()

        # 9. Seed Sample Complaints with AI Analysis & Locations
        sample_complaints_data = [
            {
                "num": "CL-2026-00101",
                "title": "Massive deep pothole near Metro Pillar 42",
                "desc": "Deep pothole on the main road right after the traffic signal. Two 2-wheelers skidded this morning.",
                "cat": "POTHOLE",
                "dept": "ROADS",
                "officer": "ROADS",
                "status": ComplaintStatus.IN_PROGRESS,
                "priority": PriorityLevel.P1,
                "severity": SeverityLevel.CRITICAL,
                "lat": 28.6328,
                "lng": 77.2197,
                "addr": "Outer Circle, Connaught Place, New Delhi"
            },
            {
                "num": "CL-2026-00102",
                "title": "Overflowing garbage dump outside market entrance",
                "desc": "Garbage has not been picked up for 4 days. Strong foul smell and stray animals blocking entry.",
                "cat": "GARBAGE",
                "dept": "SANITATION",
                "officer": "SANITATION",
                "status": ComplaintStatus.ASSIGNED,
                "priority": PriorityLevel.P2,
                "severity": SeverityLevel.HIGH,
                "lat": 28.6360,
                "lng": 77.2250,
                "addr": "Bengali Market, New Delhi"
            },
            {
                "num": "CL-2026-00103",
                "title": "Streetlight cluster dark for entire residential stretch",
                "desc": "Five continuous streetlights not working on Road No 3. Very dark and unsafe for pedestrians at night.",
                "cat": "STREETLIGHT",
                "dept": "ELECTRICAL",
                "officer": "ELECTRICAL",
                "status": ComplaintStatus.SUBMITTED,
                "priority": PriorityLevel.P3,
                "severity": SeverityLevel.MEDIUM,
                "lat": 28.6410,
                "lng": 77.2110,
                "addr": "Janpath Road, New Delhi"
            },
            {
                "num": "CL-2026-00104",
                "title": "Open manhole with missing cover near school",
                "desc": "Chamber cover broken. Open manhole pit right in front of the school gate. Immediate accident risk!",
                "cat": "OPEN_MANHOLE",
                "dept": "MANHOLE",
                "officer": None,
                "status": ComplaintStatus.ROUTED,
                "priority": PriorityLevel.P1,
                "severity": SeverityLevel.CRITICAL,
                "lat": 28.6290,
                "lng": 77.2180,
                "addr": "Barakhamba Road, New Delhi"
            },
            {
                "num": "CL-2026-00105",
                "title": "Main water pipeline burst leaking clean water",
                "desc": "Water pipeline burst under footpath. Fresh drinking water flooding the street since early morning.",
                "cat": "WATER_LEAKAGE",
                "dept": "WATER",
                "officer": None,
                "status": ComplaintStatus.RESOLVED,
                "priority": PriorityLevel.P2,
                "severity": SeverityLevel.HIGH,
                "lat": 28.6345,
                "lng": 77.2155,
                "addr": "KG Marg, New Delhi"
            }
        ]

        for item in sample_complaints_data:
            c = Complaint(
                complaint_number=item["num"],
                citizen_id=citizen.id,
                category_id=cat_map[item["cat"]].id,
                department_id=dept_map[item["dept"]].id,
                jurisdiction_id=jur_list[0].id,
                assigned_officer_id=officer_map[item["officer"]].id if item["officer"] and item["officer"] in officer_map else None,
                title=item["title"],
                description=item["desc"],
                status=item["status"],
                priority=item["priority"],
                severity=item["severity"],
                ai_analyzed=True,
                ai_status=AIStatus.COMPLETED,
                is_duplicate=False,
                resolution_rating=5 if item["status"] == ComplaintStatus.RESOLVED else None,
                citizen_verified=True if item["status"] == ComplaintStatus.RESOLVED else None,
                created_at=datetime.now(timezone.utc) - timedelta(days=2)
            )
            session.add(c)
            await session.flush()

            # Location
            loc = ComplaintLocation(
                complaint_id=c.id,
                latitude=item["lat"],
                longitude=item["lng"],
                accuracy_meters=5.0,
                address=item["addr"],
                city="New Delhi",
                state="Delhi",
                postal_code="110001"
            )
            session.add(loc)

            # AI Analysis record
            ai_record = ComplaintAIAnalysis(
                complaint_id=c.id,
                model_name="civiclens-multimodal-classifier",
                model_version="1.2.0",
                detected_category=item["cat"],
                confidence=0.94,
                predicted_severity=item["severity"],
                predicted_priority=item["priority"],
                predicted_department=dept_map[item["dept"]].name,
                duplicate_candidates_count=0,
                explanation_text=f"AI confirmed '{item['cat']}' with 94% confidence. Assigned {item['priority'].value} priority due to {item['severity'].value} severity rating on major road.",
                inference_latency_ms=185.4
            )
            session.add(ai_record)

            # Status history
            hist = ComplaintStatusHistory(
                complaint_id=c.id,
                changed_by_user_id=citizen_user.id,
                previous_status=None,
                new_status=item["status"],
                reason="Initial creation & triage"
            )
            session.add(hist)

        await session.commit()
        print("Database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
