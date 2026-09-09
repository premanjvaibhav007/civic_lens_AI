import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from backend.app.models.entities import (
    Complaint, ComplaintAIAnalysis, ComplaintLocation, ComplaintImage,
    Category, Department, Jurisdiction, RoutingRule, DuplicateCandidate,
    ComplaintStatus, SeverityLevel, PriorityLevel, AIStatus, DuplicateStatus
)
from ai.models.classifier import issue_classifier
from ai.models.severity import severity_estimator
from ai.models.duplicate_detector import duplicate_detector
from ai.models.priority_engine import priority_engine
from ai.models.civic_impact_scorer import civic_impact_scorer
from backend.app.services.audit_service import audit_service
from backend.app.services.notification_service import notification_service
from backend.app.adapters.authority_adapter import get_authority_adapter
from backend.app.services.incident_service import IncidentService

logger = logging.getLogger("civiclens.ai")

class AIService:
    @staticmethod
    async def analyze_complaint(
        db: AsyncSession,
        complaint_id: str
    ) -> Optional[ComplaintAIAnalysis]:
        """
        Asynchronous AI analysis pipeline:
        1. Fetch complaint, location, image
        2. Issue classification
        3. Multimodal severity estimation
        4. Spatial-temporal duplicate detection
        5. Routing & department resolution
        6. Explainable priority calculation
        7. State transition & audit
        """
        start_time = time.time()
        # Fetch complaint with eager citizen relationship
        stmt = (
            select(Complaint)
            .options(
                selectinload(Complaint.citizen),
                selectinload(Complaint.department)
            )
            .where(Complaint.id == complaint_id)
        )
        result = await db.execute(stmt)
        complaint = result.scalars().first()
        if not complaint:
            logger.error(f"[AIService] Complaint {complaint_id} not found")
            return None

        # Fetch location
        loc_stmt = select(ComplaintLocation).where(ComplaintLocation.complaint_id == complaint_id)
        loc_res = await db.execute(loc_stmt)
        location = loc_res.scalars().first()

        # Fetch primary image
        img_stmt = select(ComplaintImage).where(ComplaintImage.complaint_id == complaint_id, ComplaintImage.is_primary == True)
        img_res = await db.execute(img_stmt)
        primary_image = img_res.scalars().first()

        image_path = None
        if primary_image:
            # Check local file path if stored locally
            filename = primary_image.image_url.split("/")[-1]
            candidate_path = f"./storage/uploads/{filename}"
            image_path = candidate_path

        # Spam & Fraud Detection Check
        from backend.app.services.spam_detection_service import spam_detection_service
        spam_result = await spam_detection_service.evaluate_complaint(
            db=db,
            citizen_id=complaint.citizen_id,
            title=complaint.title,
            description=complaint.description,
            image_hash=primary_image.image_hash if primary_image else None
        )
        if spam_result.requires_manual_review:
            complaint.requires_manual_verification = True

        try:
            # 1. Issue classification with Confidence Tiers
            detected_category_code, confidence, confidence_tier, probabilities, visual_features = (
                issue_classifier.classify_with_confidence_tiers(
                    text=f"{complaint.title} {complaint.description or ''}",
                    image_source=image_path
                )
            )
            if confidence_tier == "LOW":
                complaint.requires_manual_verification = True

            # Extract visual embedding for duplicate similarity
            new_embedding = issue_classifier.embedding_extractor.extract_embedding(image_path) if image_path else None

            # Match detected category with DB Category table
            cat_stmt = select(Category).where(Category.code == detected_category_code)
            cat_res = await db.execute(cat_stmt)
            matched_category = cat_res.scalars().first()

            if matched_category:
                complaint.category_id = matched_category.id

            # 2. Multimodal Severity Estimation
            is_major = "road" in (location.address or "").lower() if location else False
            severity, comp_sev_score, sev_factors = severity_estimator.estimate_severity(
                category=detected_category_code,
                text=f"{complaint.title} {complaint.description or ''}",
                visual_features=visual_features,
                is_major_road=is_major
            )
            complaint.severity = severity

            # 3. Duplicate Detection
            duplicate_candidates_data = []
            if location:
                # Fetch active complaints in same city or within bounding area
                active_stmt = (
                    select(Complaint, ComplaintLocation, ComplaintImage, Category)
                    .join(ComplaintLocation, Complaint.id == ComplaintLocation.complaint_id)
                    .outerjoin(ComplaintImage, and_(Complaint.id == ComplaintImage.complaint_id, ComplaintImage.is_primary == True))
                    .outerjoin(Category, Complaint.category_id == Category.id)
                    .where(
                        Complaint.id != complaint_id,
                        Complaint.status.in_([
                            ComplaintStatus.SUBMITTED,
                            ComplaintStatus.AI_VERIFIED,
                            ComplaintStatus.ROUTED,
                            ComplaintStatus.ASSIGNED,
                            ComplaintStatus.IN_PROGRESS
                        ])
                    )
                )
                active_res = await db.execute(active_stmt)
                rows = active_res.all()

                active_list = []
                for comp_row, loc_row, img_row, cat_row in rows:
                    active_list.append({
                        "id": comp_row.id,
                        "complaint_number": comp_row.complaint_number,
                        "title": comp_row.title,
                        "description": comp_row.description,
                        "status": comp_row.status.value,
                        "latitude": loc_row.latitude,
                        "longitude": loc_row.longitude,
                        "category": cat_row.code if cat_row else "",
                        "created_at": comp_row.created_at,
                        "primary_image_url": img_row.image_url if img_row else None,
                        "image_hash": img_row.image_hash if img_row else None
                    })

                new_comp_dict = {
                    "id": complaint.id,
                    "title": complaint.title,
                    "description": complaint.description,
                    "category": detected_category_code,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "created_at": complaint.created_at,
                    "image_hash": primary_image.image_hash if primary_image else None
                }

                duplicate_candidates_data = duplicate_detector.find_duplicates(new_comp_dict, active_list)

                # Persist duplicate candidate records
                for dup in duplicate_candidates_data:
                    dup_record = DuplicateCandidate(
                        complaint_id=complaint_id,
                        candidate_complaint_id=dup["candidate_complaint_id"],
                        similarity_score=dup["similarity_score"],
                        image_similarity=dup["image_similarity"],
                        text_similarity=dup["text_similarity"],
                        geo_distance_meters=dup["geo_distance_meters"],
                        status=DuplicateStatus.POTENTIAL
                    )
                    db.add(dup_record)

                if duplicate_candidates_data and duplicate_candidates_data[0]["similarity_score"] >= 0.80:
                    complaint.is_duplicate = True
                    complaint.duplicate_score = duplicate_candidates_data[0]["similarity_score"]
                    complaint.duplicate_of_id = duplicate_candidates_data[0]["candidate_complaint_id"]

            # 4. Department & Jurisdiction Routing
            target_department = None
            # Check explicit routing rules
            if matched_category:
                route_stmt = select(RoutingRule).where(
                    RoutingRule.category_id == matched_category.id,
                    RoutingRule.is_active == True
                )
                route_res = await db.execute(route_stmt)
                active_rule = route_res.scalars().first()
                if active_rule:
                    dept_stmt = select(Department).where(Department.id == active_rule.target_department_id)
                    dept_res = await db.execute(dept_stmt)
                    target_department = dept_res.scalars().first()

                if not target_department and matched_category.default_department_id:
                    dept_stmt = select(Department).where(Department.id == matched_category.default_department_id)
                    dept_res = await db.execute(dept_stmt)
                    target_department = dept_res.scalars().first()

            if not target_department:
                # Fallback to category default department name lookup
                suggested_dept_name = visual_features.get("suggested_department", "Municipal Roads Department")
                dept_stmt = select(Department).where(Department.name.ilike(f"%{suggested_dept_name.split()[0]}%"))
                dept_res = await db.execute(dept_stmt)
                target_department = dept_res.scalars().first()

            if target_department:
                complaint.department_id = target_department.id

            # Match or assign nearest jurisdiction ward
            if location and location.city:
                jur_stmt = select(Jurisdiction).where(Jurisdiction.city.ilike(f"%{location.city}%"))
                jur_res = await db.execute(jur_stmt)
                matched_jur = jur_res.scalars().first()
                if matched_jur:
                    complaint.jurisdiction_id = matched_jur.id

            # 5. Explainable Priority Calculation
            priority, p_score, p_factors, narrative = priority_engine.calculate_priority(
                severity=complaint.severity,
                category=detected_category_code,
                is_major_road=is_major,
                duplicate_count=len(duplicate_candidates_data),
                age_days=0
            )
            complaint.priority = priority

            # 5b. Civic Impact Score (0–100 with explainable breakdown)
            impact_breakdown_obj = civic_impact_scorer.compute(
                category_code=detected_category_code,
                description=f"{complaint.title} {complaint.description or ''}",
                severity=severity.value,
                days_open=0,
                report_count=1 + len(duplicate_candidates_data),
                recurrence_count=0,
                duplicate_count=len(duplicate_candidates_data),
            )
            civic_impact_score = impact_breakdown_obj.total_score
            impact_breakdown_dict = {
                "safety": impact_breakdown_obj.safety_score,
                "population": impact_breakdown_obj.population_score,
                "traffic": impact_breakdown_obj.traffic_score,
                "persistence": impact_breakdown_obj.persistence_score,
                "recurrence": impact_breakdown_obj.recurrence_score,
                "total": civic_impact_score,
                "factors": impact_breakdown_obj.factors,
                "explanation": impact_breakdown_obj.explanation,
            }

            # 6. Save AI Analysis Record
            latency_ms = (time.time() - start_time) * 1000.0
            ai_status = AIStatus.COMPLETED if confidence >= 0.50 else AIStatus.LOW_CONFIDENCE

            ai_analysis = ComplaintAIAnalysis(
                complaint_id=complaint_id,
                model_name=issue_classifier.model_name,
                model_version=issue_classifier.model_version,
                detected_category=detected_category_code,
                confidence=confidence,
                predicted_severity=severity,
                predicted_priority=priority,
                predicted_department=target_department.name if target_department else "Municipal Administration",
                duplicate_candidates_count=len(duplicate_candidates_data),
                contributing_factors={
                    "severity_factors": sev_factors,
                    "priority_factors": p_factors,
                    "probabilities": probabilities,
                    "civic_impact": impact_breakdown_dict,
                },
                explanation_text=narrative + f" Civic Impact: {civic_impact_score}/100. {impact_breakdown_obj.explanation}",
                raw_inference_json={
                    "probabilities": probabilities,
                    "visual_features": visual_features,
                    "civic_impact_score": civic_impact_score,
                },
                inference_latency_ms=latency_ms
            )
            db.add(ai_analysis)

            # 7. Incident Clustering — link complaint to existing incident or create new one
            try:
                nearby_incident = await IncidentService.find_nearby_open_incident(
                    db=db,
                    lat=location.latitude if location else 0.0,
                    lng=location.longitude if location else 0.0,
                    category_code=detected_category_code,
                ) if location else None

                if nearby_incident:
                    await IncidentService.link_complaint_to_incident(
                        db=db,
                        complaint=complaint,
                        incident=nearby_incident,
                        similarity_score=duplicate_candidates_data[0]["similarity_score"] if duplicate_candidates_data else 0.85,
                    )
                    await IncidentService.update_civic_impact(
                        db=db,
                        incident=nearby_incident,
                        impact_score=max(civic_impact_score, nearby_incident.civic_impact_score),
                        impact_breakdown=impact_breakdown_dict,
                        explanation=impact_breakdown_obj.explanation,
                    )
                else:
                    new_incident = await IncidentService.create_incident_from_complaint(
                        db=db,
                        complaint=complaint,
                        ai_analysis=ai_analysis,
                        location=location,
                    )
                    await IncidentService.update_civic_impact(
                        db=db,
                        incident=new_incident,
                        impact_score=civic_impact_score,
                        impact_breakdown=impact_breakdown_dict,
                        explanation=impact_breakdown_obj.explanation,
                    )
            except Exception as inc_err:
                logger.warning(f"[AIService] Incident clustering non-fatal error: {inc_err}")

            # Update Complaint State
            complaint.ai_analyzed = True
            complaint.ai_status = ai_status
            complaint.status = ComplaintStatus.ROUTED

            # Dispatch to Authority Adapter
            adapter = get_authority_adapter("dashboard")
            await adapter.dispatch_complaint({
                "complaint_number": complaint.complaint_number,
                "title": complaint.title,
                "department_name": target_department.name if target_department else "General",
                "priority": complaint.priority.value,
                "severity": complaint.severity.value
            })

            # Notify Citizen
            if complaint.citizen and complaint.citizen.user_id:
                await notification_service.create_notification(
                    db=db,
                    user_id=complaint.citizen.user_id,
                    title=f"Complaint {complaint.complaint_number} Analyzed & Routed",
                    message=f"AI detected '{detected_category_code}' ({int(confidence*100)}% confidence). Routed to {target_department.name if target_department else 'Civic Authority'}.",
                    complaint_id=complaint.id,
                    notification_type="AI_ROUTED"
                )

            await audit_service.log_event(
                db=db,
                action="AI_ANALYSIS_COMPLETED",
                entity_name="Complaint",
                entity_id=complaint.id,
                new_value={
                    "status": complaint.status.value,
                    "category": detected_category_code,
                    "severity": complaint.severity.value,
                    "priority": complaint.priority.value,
                    "department": target_department.name if target_department else None
                }
            )

            await db.commit()
            logger.info(f"[AIService] Analysis completed in {latency_ms:.1f}ms for {complaint.complaint_number}")
            return ai_analysis

        except Exception as e:
            logger.error(f"[AIService] AI Analysis failed for complaint {complaint_id}: {e}", exc_info=True)
            # Graceful fallback: Never crash the submission or block authority workflow
            complaint.ai_analyzed = True
            complaint.ai_status = AIStatus.FAILED
            complaint.status = ComplaintStatus.SUBMITTED
            complaint.requires_manual_verification = True
            await db.commit()
            return None

    @staticmethod
    def verify_resolution_visual(
        before_image_path: Optional[str],
        after_image_path: Optional[str]
    ) -> Dict[str, Any]:
        """
        Stage 7: Resolution Verification AI.
        Compares before and after images to verify physical resolution.
        Returns visual difference score (0–100), likely_resolved flag, and confidence.
        """
        import os
        from PIL import Image
        import numpy as np

        if not before_image_path or not after_image_path:
            return {
                "diff_score": 0.0,
                "likely_resolved": True,
                "confidence": 0.5,
                "explanation": "Visual comparison skipped: before or after photo unavailable."
            }

        try:
            if not os.path.exists(before_image_path) or not os.path.exists(after_image_path):
                return {
                    "diff_score": 0.0,
                    "likely_resolved": True,
                    "confidence": 0.5,
                    "explanation": "Visual comparison skipped: photo files not found locally."
                }

            b_img = Image.open(before_image_path).convert("L").resize((256, 256))
            a_img = Image.open(after_image_path).convert("L").resize((256, 256))

            b_arr = np.array(b_img, dtype=np.float32)
            a_arr = np.array(a_img, dtype=np.float32)

            # Mean Absolute Pixel Difference percentage
            abs_diff = np.abs(b_arr - a_arr)
            mae = float(np.mean(abs_diff))
            diff_score = round(min(100.0, (mae / 255.0) * 100.0 * 2.5), 1)

            # Identical image uploaded (diff < 3%) is suspicious/fraudulent
            if diff_score < 3.0:
                likely_resolved = False
                confidence = 0.90
                explanation = "Suspicious resolution evidence: identical photo was submitted."
            # High difference indicates genuine physical change/repair in the scene
            elif 15.0 <= diff_score <= 85.0:
                likely_resolved = True
                confidence = 0.85
                explanation = f"Physical alteration detected with {diff_score}% visual difference, consistent with infrastructure repair."
            else:
                likely_resolved = True
                confidence = 0.70
                explanation = f"Scene comparison computed with {diff_score}% difference."

            return {
                "diff_score": diff_score,
                "likely_resolved": likely_resolved,
                "confidence": confidence,
                "explanation": explanation
            }
        except Exception as e:
            logger.warning(f"Resolution visual verification error: {e}")
            return {
                "diff_score": 0.0,
                "likely_resolved": True,
                "confidence": 0.5,
                "explanation": f"Visual verification fallback: {e}"
            }

ai_service = AIService()
