"""Client-facing portal endpoints: an aggregated consultancy status summary.
Org-scoped and membership-validated (works for both client users and crew)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_organization_context
from app.models.models import OrganizationUser
from app.services.portal.summary_service import build_summary

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/summary")
def get_portal_summary(
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context),
):
    """Aggregated status of the consultancy engagement for the active organization."""
    return build_summary(db, org_ctx.organization_id, org_ctx.user)
