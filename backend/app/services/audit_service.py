from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.entities import AuditLog

class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        action: str,
        entity_name: str,
        entity_id: str,
        user_id: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_name=entity_name,
            entity_id=entity_id,
            old_value_json=old_value,
            new_value_json=new_value,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(audit_entry)
        await db.flush()
        return audit_entry

audit_service = AuditService()
