from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.models import Roadmap, RoadmapItem, Workspace, OrganizationUser
from app.schemas.schemas import RoadmapOut, RoadmapItemOut, RoadmapItemUpdate
from app.dependencies import get_organization_context, RoleChecker

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])

@router.get("/latest", response_model=Optional[RoadmapOut])
def get_latest_roadmap(
    workspace_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    Get the latest execution roadmap generated for the workspace.
    """
    # Verify workspace belongs to organization
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    latest_roadmap = db.query(Roadmap).filter(
        Roadmap.workspace_id == workspace_id
    ).order_by(Roadmap.created_at.desc()).first()
    
    return latest_roadmap

@router.patch("/items/{item_id}", response_model=RoadmapItemOut)
def update_roadmap_item(
    item_id: int,
    item_in: RoadmapItemUpdate,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(["CLIENT_OWNER", "CLIENT_EXECUTIVE", "CLIENT_MANAGER", "CONSULTANT"]))
):
    """
    Update progress status, assignment, or due dates of a roadmap action item.
    """
    # Join with Roadmap to verify organization ownership
    item = db.query(RoadmapItem).join(Roadmap).filter(
        RoadmapItem.id == item_id,
        Roadmap.organization_id == org_ctx.organization_id
    ).first()
    
    if not item:
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
