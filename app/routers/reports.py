import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Diagnosis, Roadmap, RoadmapItem, Workspace, OrganizationUser
from app.dependencies import get_organization_context
from app.policy.deps import get_principal, require_action
from app.policy.principal import Principal
from app.policy import Action, ObjectType

router = APIRouter(prefix="/reports", tags=["reports"])

# States of a Diagnosis/Roadmap that are shareable with a CLIENT_USER. The
# executive brief composes from these two models (which carry their own
# `visibility` string column, distinct from the §8 ObjectType.REPORT whitelist),
# so we match against the project's diagnosis/roadmap state vocabulary directly.
_CLIENT_VISIBLE_REPORT_STATES = frozenset({"APPROVED", "CLIENT_VISIBLE", "CLIENT_SHARED"})


@router.get("/executive-brief")
def get_executive_brief(
    workspace_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context),
    principal: Principal = Depends(require_action(Action.VIEW_APPROVED_REPORTS)),
):
    """
    Generate and retrieve a consolidated executive consulting brief containing
    the latest SWOT, recommendations, and active roadmap items.

    POLICY (Fase 3 wiring): gated on Action.VIEW_APPROVED_REPORTS (ejes 1+2:
    org-scope + role). The brief is composed from Diagnosis + Roadmap, which may
    sit in internal states (INTERNAL_ONLY, DRAFT_INTERNAL). For a CLIENT_USER the
    composition is restricted to client-visible material (eje 3):
      - the latest CLIENT-VISIBLE diagnosis only (an internal latest one yields
        404, never a leak of internal SWOT/findings);
      - a CLIENT-VISIBLE roadmap, with INTERNAL_ONLY items dropped.
    Crew/superadmin compose from the latest diagnosis/roadmap unconditionally.
    """
    # Verify workspace belongs to organization (org-scope, eje 1)
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    org_id = org_ctx.organization_id
    is_client = principal.is_client and not principal.is_superadmin

    # --- Pick the diagnosis the caller is allowed to compose from ---
    diag_q = db.query(Diagnosis).filter(
        Diagnosis.workspace_id == workspace_id,
        Diagnosis.organization_id == org_id,
    )
    if is_client:
        diag_q = diag_q.filter(Diagnosis.visibility.in_(_CLIENT_VISIBLE_REPORT_STATES))
    latest_diag = diag_q.order_by(Diagnosis.created_at.desc()).first()

    if not latest_diag:
        # For a client this is also reached when only internal diagnoses exist:
        # we return the "no diagnosis" response rather than expose internal
        # material — the client-visible query simply found nothing.
        raise HTTPException(
            status_code=400,
            detail="No business diagnosis has been run for this workspace yet."
        )

    # --- Pick the roadmap the caller is allowed to compose from ---
    roadmap_q = db.query(Roadmap).filter(
        Roadmap.workspace_id == workspace_id,
        Roadmap.organization_id == org_id,
    )
    if is_client:
        roadmap_q = roadmap_q.filter(Roadmap.visibility.in_(_CLIENT_VISIBLE_REPORT_STATES))
    latest_roadmap = roadmap_q.order_by(Roadmap.created_at.desc()).first()

    # --- Roadmap items: drop internal items for clients ---
    if latest_roadmap is not None:
        items = latest_roadmap.items
        if is_client:
            visible_item_states = _client_visible_roadmap_item_states()
            items = [it for it in items if it.visibility in visible_item_states]
    else:
        items = []

    # Compile report structure
    report_data = {
        "workspace_name": workspace.name,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "organization": org_ctx.organization.name,
        "diagnosis_status": latest_diag.status,
        "dimensions": [
            {
                "name": dim.name,
                "rating": dim.rating,
                "findings": dim.findings,
                "recommendations": dim.recommendations,
                "swot": dim.swot_analysis
            }
            for dim in latest_diag.dimensions
        ],
        "roadmap": {
            "created_at": latest_roadmap.created_at.isoformat() if latest_roadmap else None,
            "items": [
                {
                    "title": item.title,
                    "description": item.description,
                    "dimension": item.dimension,
                    "phase": item.phase,
                    "status": item.status,
                    "due_date": item.due_date.isoformat() if item.due_date else None
                }
                for item in items
            ]
        }
    }

    return report_data


def _client_visible_roadmap_item_states() -> frozenset:
    """Roadmap-item states a CLIENT_USER may see, from the policy whitelist."""
    from app.policy.visibility import client_visible_states
    return client_visible_states(ObjectType.ROADMAP_ITEM)
