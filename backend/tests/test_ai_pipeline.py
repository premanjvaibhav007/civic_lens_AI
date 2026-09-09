import pytest
from datetime import datetime, timezone, timedelta
from ai.models.classifier import issue_classifier
from ai.models.severity import severity_estimator
from ai.models.duplicate_detector import duplicate_detector, haversine_distance_meters
from ai.models.priority_engine import priority_engine
from backend.app.models.entities import SeverityLevel, PriorityLevel

def test_classifier_keyword_pothole():
    text = "Large crater and deep pothole on the road causing traffic blockage"
    cat, conf, probs, feats = issue_classifier.classify(text)
    assert cat in ("POTHOLE", "DAMAGED_ROAD")
    assert conf > 0.40
    assert "suggested_department" in feats

def test_classifier_keyword_garbage():
    text = "Overflowing garbage dustbin and rotting trash outside the school"
    cat, conf, probs, feats = issue_classifier.classify(text)
    assert cat == "GARBAGE"
    assert conf > 0.40

def test_classifier_keyword_streetlight():
    text = "Dark street lamp broken and not lighting up at night"
    cat, conf, probs, feats = issue_classifier.classify(text)
    assert cat == "STREETLIGHT"
    assert conf > 0.40

def test_severity_estimator_critical():
    sev, score, factors = severity_estimator.estimate_severity(
        category="OPEN_MANHOLE",
        text="Fatal accident danger, live open pit on highway!",
        visual_features={"valid": False},
        is_major_road=True
    )
    assert sev in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
    assert score >= 0.70

def test_severity_estimator_low():
    sev, score, factors = severity_estimator.estimate_severity(
        category="DAMAGED_SIGN",
        text="Minor cosmetic paint scratch on small signboard",
        visual_features={"valid": False},
        is_major_road=False
    )
    assert sev in (SeverityLevel.LOW, SeverityLevel.MEDIUM)
    assert score <= 0.60

def test_haversine_distance():
    # CP to Bengali Market (~1 km)
    dist = haversine_distance_meters(28.6328, 77.2197, 28.6360, 77.2250)
    assert 500.0 < dist < 1200.0

def test_duplicate_detector():
    now = datetime.now(timezone.utc)
    new_comp = {
        "id": "new-1",
        "title": "Deep dangerous pothole",
        "description": "Pothole near pillar 42",
        "category": "POTHOLE",
        "latitude": 28.6328,
        "longitude": 77.2197,
        "created_at": now
    }
    
    # Very close duplicate (20 meters away, same category & keywords)
    active_comps = [
        {
            "id": "old-1",
            "complaint_number": "CL-2026-0001",
            "title": "Huge pothole on road",
            "description": "Dangerous pothole near pillar 42",
            "category": "POTHOLE",
            "latitude": 28.6329,
            "longitude": 77.2198,
            "created_at": now - timedelta(hours=2),
            "status": "IN_PROGRESS"
        },
        {
            "id": "old-2",
            "complaint_number": "CL-2026-0002",
            "title": "Broken streetlight lamp",
            "description": "Streetlight off",
            "category": "STREETLIGHT",
            "latitude": 28.6900,
            "longitude": 77.3000,
            "created_at": now - timedelta(days=5),
            "status": "SUBMITTED"
        }
    ]

    duplicates = duplicate_detector.find_duplicates(new_comp, active_comps)
    assert len(duplicates) >= 1
    assert duplicates[0]["candidate_complaint_id"] == "old-1"
    assert duplicates[0]["similarity_score"] >= 0.70

def test_priority_engine():
    prio, score, factors, narrative = priority_engine.calculate_priority(
        severity=SeverityLevel.CRITICAL,
        category="OPEN_MANHOLE",
        is_major_road=True,
        duplicate_count=3,
        age_days=2
    )
    assert prio == PriorityLevel.P1
    assert "Assigned P1" in narrative
    assert len(factors) >= 3
