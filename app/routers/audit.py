from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import AuditLog, OrganizationUser
from app.schemas.schemas import AuditLogOut
from app.dependencies import RoleChecker

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("", response_model=List[AuditLogOut])
def get_audit_logs(
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(["CLIENT_OWNER", "CLIENT_EXECUTIVE", "CONSULTANT"]))
):
    """
    Retrieve compliance audit logs for the current organization.
    """
    logs = db.query(AuditLog).filter(
        AuditLog.organization_id == org_ctx.organization_id
    ).order_by(AuditLog.created_at.desc()).limit(100).all()
    
    return logs
