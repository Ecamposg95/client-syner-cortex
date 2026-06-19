from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.models import Roadmap, RoadmapItem, Workspace, OrganizationUser
from app.schemas.schemas import RoadmapOut, RoadmapItemOut, RoadmapItemUpdate
from app.dependencies import get_current_org_id, get_organization_context, RoleChecker
from app.policy import Action, ObjectType
from app.policy.deps import get_principal, require_action
from app.policy.engine import can_view
from app.policy.principal import Principal

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])

@router.get("/latest", response_model=Optional[RoadmapOut])
def get_latest_roadmap(
    workspace_id: int,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(get_principal),
):
    """
    Get the latest execution roadmap generated for the workspace.

    Eje 3 (object visibility): for a CLIENT_USER the roadmap is a shareable
    object whose items carry per-state visibility (ObjectType.ROADMAP_ITEM).
    Previously this returned the most-recent roadmap of the workspace with NO
    visibility filter, leaking INTERNAL_ONLY roadmaps and items to clients.

    Now, for a CLIENT_USER:
      (a) the container roadmap must itself be client-visible — if the latest
          roadmap is internal we 404 (never expose its existence or content);
      (b) only the client-visible items inside it are returned (the rest are
          filtered out in the response).
    Crew/superadmin see everything within scope (behaviour-preserving).
    """
    # Eje 1: workspace must belong to the active organization.
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    latest_roadmap = db.query(Roadmap).filter(
        Roadmap.workspace_id == workspace_id
    ).order_by(Roadmap.created_at.desc()).first()

    if not latest_roadmap:
        return None

    # Crew/superadmin: no per-object narrowing, return as-is.
    if principal.is_crew or principal.is_superadmin:
        return latest_roadmap

    # CLIENT_USER (Eje 3): the container itself must be client-visible. We gauge
    # the container with the ROADMAP_ITEM whitelist (CLIENT_VISIBLE/CLIENT_ASSIGNED/
    # COMPLETED) — an internal/draft/approved-but-not-shared roadmap is hidden.
    # Hiding = 404 so a client cannot infer that an internal roadmap exists.
    if not can_view(
        principal, ObjectType.ROADMAP_ITEM, latest_roadmap.visibility, org_id=org_id
    ):
        raise HTTPException(status_code=404, detail="Roadmap not found")

    # Return only the items the client may see; build the response explicitly so
    # the filtered item list (not the raw relationship) is what gets serialized.
    visible_items = [
        item for item in latest_roadmap.items
        if can_view(principal, ObjectType.ROADMAP_ITEM, item.visibility, org_id=org_id)
    ]
    return RoadmapOut(
        id=latest_roadmap.id,
        workspace_id=latest_roadmap.workspace_id,
        organization_id=latest_roadmap.organization_id,
        diagnosis_id=latest_roadmap.diagnosis_id,
        visibility=latest_roadmap.visibility,
        created_at=latest_roadmap.created_at,
        items=[RoadmapItemOut.model_validate(it) for it in visible_items],
    )

@router.patch("/items/{item_id}", response_model=RoadmapItemOut)
def update_roadmap_item(
    item_id: int,
    item_in: RoadmapItemUpdate,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    # Eje 2: UPDATE_TASKS is the §8 lane for editing task/roadmap progress. It is
    # ALLOW for crew and CONDITIONAL for the client OWNER/EXECUTIVE tier; the old
    # ad-hoc role list is a subset, so admitted callers keep access while the gate
    # now derives from the matrix.
    principal: Principal = Depends(require_action(Action.UPDATE_TASKS)),
):
    """
    Update progress status, assignment, or due dates of a roadmap action item.

    Eje 3: a CLIENT_USER may only mutate items they can see (client-visible
    states such as CLIENT_ASSIGNED — their own tasks). An internal item is
    invisible, so a client touching it 404s exactly as if it did not exist.
    Crew/superadmin may touch any item within scope.
    """
    # Eje 1: join with Roadmap to verify organization ownership.
    item = db.query(RoadmapItem).join(Roadmap).filter(
        RoadmapItem.id == item_id,
        Roadmap.organization_id == org_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Roadmap action item not found")

    # Eje 3: clients can only mutate items visible to them. Hidden -> 404.
    if not (principal.is_crew or principal.is_superadmin):
        if not can_view(
            principal, ObjectType.ROADMAP_ITEM, item.visibility, org_id=org_id
        ):
            raise HTTPException(status_code=404, detail="Roadmap action item not found")

    # Update fields if provided
    if item_in.status is not None:
        if item_in.status not in ["TODO", "IN_PROGRESS", "DONE"]:
            raise HTTPException(status_code=400, detail="Invalid status value. Must be TODO, IN_PROGRESS, or DONE.")
        item.status = item_in.status

    if item_in.assigned_to is not None:
        item.assigned_to = item_in.assigned_to

    if item_in.due_date is not None:
        item.due_date = item_in.due_date

    import datetime
    item.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item
