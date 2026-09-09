"""
Spam & Fraud Detection Service — Stage 4
Protects the platform from report bursts, automated bot spam,
and recycled fraudulent photo submissions.
"""
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, NamedTuple, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.models.entities import Complaint, ComplaintImage, Citizen
from backend.app.core.config import settings

logger = logging.getLogger("civiclens.spam_detection")


class SpamCheckResult(NamedTuple):
    is_spam: bool
    requires_manual_review: bool
    reason: Optional[str]
    risk_score: float  # 0.0 to 1.0


class SpamDetectionService:

    @staticmethod
    def check_text_quality(title: str, description: Optional[str] = None) -> Tuple[bool, Optional[str], float]:
        """
        Detects repetitive keyboard mashing or meaningless noise (e.g. 'asdfasdfasdf').
        """
        combined = f"{title} {description or ''}".strip().lower()
        if len(combined) < 5:
            return True, "Report description is too short to be informative.", 0.85

        # Check repetitive characters (e.g. 'aaaaaaa' or 'zzzzzzzz')
        if re.search(r'(.)\1{5,}', combined):
            return True, "Repetitive character sequence detected.", 0.90

        # Check repeating pattern of 2-3 characters (e.g. 'asdfasdfasdf')
        if re.search(r'(.{2,4})\1{4,}', combined):
            return True, "Repeated character pattern detected.", 0.85

        return False, None, 0.0

    @staticmethod
    async def check_submission_burst(
        db: AsyncSession,
        citizen_id: str,
        max_per_hour: int = 5
    ) -> Tuple[bool, Optional[str], float]:
        """
        Checks if a single citizen account has exceeded the hourly submission threshold.
        """
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        stmt = select(func.count(Complaint.id)).where(
            Complaint.citizen_id == citizen_id,
            Complaint.created_at >= one_hour_ago
        )
        res = await db.execute(stmt)
        count = res.scalar_one() or 0

        if count >= max_per_hour:
            return True, f"Account submission rate exceeded limit ({count}/{max_per_hour} reports this hour).", 0.95
        return False, None, 0.0

    @staticmethod
    async def check_image_reuse(
        db: AsyncSession,
        image_hash: Optional[str]
    ) -> Tuple[bool, Optional[str], float]:
        """
        Checks if the exact image hash was previously used in multiple resolved or rejected complaints.
        """
        if not image_hash:
            return False, None, 0.0

        stmt = select(func.count(ComplaintImage.id)).where(
            ComplaintImage.image_hash == image_hash
        )
        res = await db.execute(stmt)
        count = res.scalar_one() or 0

        # If the same exact image has been uploaded 3+ times before
        if count >= 3:
            return True, f"Duplicate photo pattern detected across {count} prior reports.", 0.80

        return False, None, 0.0

    @classmethod
    async def evaluate_complaint(
        cls,
        db: AsyncSession,
        citizen_id: str,
        title: str,
        description: Optional[str] = None,
        image_hash: Optional[str] = None
    ) -> SpamCheckResult:
        """
        Runs comprehensive heuristic and temporal spam evaluation.
        """
        # 1. Text quality check
        text_spam, text_reason, text_risk = cls.check_text_quality(title, description)
        if text_spam:
            logger.info(f"[SpamDetection] Flagged text spam: {text_reason}")
            return SpamCheckResult(
                is_spam=True,
                requires_manual_review=True,
                reason=text_reason,
                risk_score=text_risk
            )

        # 2. Burst rate check
        burst_spam, burst_reason, burst_risk = await cls.check_submission_burst(
            db, citizen_id, settings.SPAM_BURST_MAX_PER_HOUR
        )
        if burst_spam:
            logger.info(f"[SpamDetection] Flagged burst spam: {burst_reason}")
            return SpamCheckResult(
                is_spam=True,
                requires_manual_review=True,
                reason=burst_reason,
                risk_score=burst_risk
            )

        # 3. Image reuse check
        img_spam, img_reason, img_risk = await cls.check_image_reuse(db, image_hash)
        if img_spam:
            logger.info(f"[SpamDetection] Flagged image reuse: {img_reason}")
            return SpamCheckResult(
                is_spam=False,
                requires_manual_review=True,
                reason=img_reason,
                risk_score=img_risk
            )

        return SpamCheckResult(
            is_spam=False,
            requires_manual_review=False,
            reason=None,
            risk_score=0.0
        )


spam_detection_service = SpamDetectionService()
