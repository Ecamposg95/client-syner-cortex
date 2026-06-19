from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import AuditLog
from app.schemas.schemas import AuditLogOut
from app.dependencies import get_current_org_id
from app.policy import Action
from app.policy.deps import require_action

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get(
    "",
    response_model=List[AuditLogOut],
    # §8: VIEW_AUDIT es ALLOW solo para SYNER_ADMIN y CONDITIONAL para
    # SYNER_PARTNER (que pasa el gate). Ningún rol CLIENT_* lo tiene, así que
    # un CLIENT_USER queda fuera (403). Esto corrige la divergencia previa, que
    # exponía la auditoría a CLIENT_OWNER/CLIENT_EXECUTIVE y arrastraba el drift
    # de rol "CONSULTANT" (canónico = "SYNER_CONSULTANT").
    dependencies=[Depends(require_action(Action.VIEW_AUDIT))],
)
def get_audit_logs(
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
):
    """
    Retrieve compliance audit logs for the current organization.
    """
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
        .all()
    )

    return logs
