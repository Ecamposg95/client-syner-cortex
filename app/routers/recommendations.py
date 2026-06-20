"""Recommendations (§6) — prioritized, actionable suggestions the crew creates,
optionally shares with the client, and links to the roadmap that delivers them.

The model already exists (`app.models.recommendation.Recommendation`); this router
exposes it through the three policy axes:

  - Eje 1 (scope): every query is org-scoped via `get_current_org_id` (validated
    membership) and `scoped_query`.
  - Eje 2 (role): mutations are gated on `Action.EDIT_AI_OUTPUTS`, which the §8
    matrix grants only to Syner crew — a CLIENT_USER creating/editing 403s.
  - Eje 3 (visibility): listing/detail go through `scoped_query` /
    `can_view` with `ObjectType.RECOMMENDATION`, so a client sees only
    SHARED/TASK_VISIBLE (and EXECUTIVE_ONLY when OWNER/EXECUTIVE), never INTERNAL.

The orchestrator mounts this router under /api.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_org_id
from app.models.models import Workspace, Roadmap, RoadmapItem
from app.models.recommendation import Recommendation, RecVisibility
from app.schemas.recommendation import RecommendationCreate, RecommendationOut
from app.policy import Action, ObjectType
from app.policy.deps import get_principal, require_action, scoped_query
from app.policy.engine import can_view
from app.policy.principal import Principal

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# --------------------------------------------------------------------------- #
# Schemas (request bodies that aren't in app.schemas.recommendation)
# --------------------------------------------------------------------------- #
from pydantic import BaseModel  # noqa: E402


class RecommendationUpdate(BaseModel):
    """Partial edit. Setting visibility=SHARED is the "share with client" action."""
    text: Optional[str] = None
    dimension: Optional[str] = None
    impact: Optional[str] = None
    effort: Optional[str] = None
    visibility: Optional[RecVisibility] = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _get_visible_or_404(
    db: Session, rec_id: int, principal: Principal, org_id: int
) -> Recommendation:
    """Fetch a recommendation in the active org that the caller may see.

    Eje 1: must belong to `org_id`. Eje 3: a client only sees client-visible
    states; an internal (or out-of-org) recommendation 404s so its existence is
    never disclosed. Crew/superadmin see everything within scope.
    """
    rec = db.query(Recommendation).filter(
        Recommendation.id == rec_id,
        Recommendation.organization_id == org_id,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if not can_view(
        principal, ObjectType.RECOMMENDATION, rec.visibility.value, org_id=org_id
    ):
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec


# --------------------------------------------------------------------------- #
# Read
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[RecommendationOut])
def list_recommendations(
    dimension: Optional[str] = None,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(get_principal),
):
    """List recommendations of the active org, already visibility-filtered for
    the caller (crew see all; clients see SHARED/TASK_VISIBLE, plus EXECUTIVE_ONLY
    only for the OWNER/EXECUTIVE tier). Optional `?dimension=` narrows by axis."""
    q = scoped_query(
        db, Recommendation, principal, org_id,
        object_type=ObjectType.RECOMMENDATION,
    )
    if dimension is not None:
        q = q.filter(Recommendation.dimension == dimension)
    rows = q.order_by(Recommendation.created_at.desc()).all()

    # scoped_query whitelists EXECUTIVE_ONLY for any client, but that state is
    # gated to the OWNER/EXECUTIVE tier (Eje 3). That tier check lives in
    # can_view, not in the SQL filter, so re-apply it here: a non-executive
    # client must not receive EXECUTIVE_ONLY recommendations. Crew/superadmin
    # pass can_view unconditionally, so this is a no-op for them.
    return [
        r for r in rows
        if can_view(
            principal, ObjectType.RECOMMENDATION, r.visibility.value, org_id=org_id
        )
    ]


@router.get("/{rec_id}", response_model=RecommendationOut)
def get_recommendation(
    rec_id: int,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(get_principal),
):
    """Detail of one recommendation; 404 if not in the org or not visible."""
    return _get_visible_or_404(db, rec_id, principal, org_id)


# --------------------------------------------------------------------------- #
# Mutations (crew only — Action.EDIT_AI_OUTPUTS)
# --------------------------------------------------------------------------- #
@router.post("", response_model=RecommendationOut, status_code=status.HTTP_201_CREATED)
def create_recommendation(
    payload: RecommendationCreate,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(require_action(Action.EDIT_AI_OUTPUTS)),
):
    """Crew create a recommendation. The workspace must belong to the active org
    (Eje 1); the body's organization_id is forced to the validated org so a crew
    can't seed a recommendation into another tenant."""
    workspace = db.query(Workspace).filter(
        Workspace.id == payload.workspace_id,
        Workspace.organization_id == org_id,
    ).first()
    if not workspace:
        raise HTTPException(
            status_code=404, detail="Workspace not found in this organization"
        )

    rec = Recommendation(
        workspace_id=payload.workspace_id,
        organization_id=org_id,
        dimension=payload.dimension,
        text=payload.text,
        visibility=payload.visibility or RecVisibility.INTERNAL,
        impact=payload.impact,
        effort=payload.effort,
        linked_roadmap_item_id=payload.linked_roadmap_item_id,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.patch("/{rec_id}", response_model=RecommendationOut)
def update_recommendation(
    rec_id: int,
    payload: RecommendationUpdate,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(require_action(Action.EDIT_AI_OUTPUTS)),
):
    """Crew edit text/dimension/impact/effort/visibility. Setting
    visibility=SHARED is the "share with client" action. 404 if out of org."""
    rec = db.query(Recommendation).filter(
        Recommendation.id == rec_id,
        Recommendation.organization_id == org_id,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if payload.text is not None:
        rec.text = payload.text
    if payload.dimension is not None:
        rec.dimension = payload.dimension
    if payload.impact is not None:
        rec.impact = payload.impact
    if payload.effort is not None:
        rec.effort = payload.effort
    if payload.visibility is not None:
        rec.visibility = payload.visibility

    db.commit()
    db.refresh(rec)
    return rec


@router.post("/{rec_id}/convert-to-roadmap", response_model=RecommendationOut)
def convert_to_roadmap(
    rec_id: int,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(require_action(Action.EDIT_AI_OUTPUTS)),
):
    """Crew convert a recommendation into a roadmap action item.

    Creates the minimal RoadmapItem under the workspace's latest roadmap (or a
    new container roadmap if none exists yet), then links it back via
    `linked_roadmap_item_id`. Idempotent-ish: if already linked, returns as-is.
    """
    rec = db.query(Recommendation).filter(
        Recommendation.id == rec_id,
        Recommendation.organization_id == org_id,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if rec.linked_roadmap_item_id is not None:
        # Already converted — don't create a duplicate item.
        return rec

    # Find (or stub) a container roadmap for this workspace. Roadmap.diagnosis_id
    # is NOT NULL, so we can only attach to an EXISTING roadmap; if the workspace
    # has none yet, we surface a clear 409 instead of fabricating a diagnosis.
    roadmap = db.query(Roadmap).filter(
        Roadmap.workspace_id == rec.workspace_id,
        Roadmap.organization_id == org_id,
    ).order_by(Roadmap.created_at.desc()).first()
    if roadmap is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "No roadmap exists for this workspace yet; generate the roadmap "
                "before converting recommendations into action items."
            ),
        )

    item = RoadmapItem(
        roadmap_id=roadmap.id,
        title=(rec.text[:120] if rec.text else "Recomendación"),
        description=rec.text,
        dimension=rec.dimension or "General",
        phase=30,
        status="TODO",
        visibility="INTERNAL_ONLY",
    )
    db.add(item)
    db.flush()  # assign item.id without ending the transaction

    rec.linked_roadmap_item_id = item.id
    db.commit()
    db.refresh(rec)
    return rec
