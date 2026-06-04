from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Workspace, OrganizationUser
from app.schemas.schemas import WorkspaceCreate, WorkspaceOut
from app.dependencies import get_organization_context, RoleChecker

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("", response_model=List[WorkspaceOut])
def list_workspaces(
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    List all workspaces for the organization.
    """
    workspaces = db.query(Workspace).filter(Workspace.organization_id == org_ctx.organization_id).all()
    return workspaces

@router.post("", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace_in: WorkspaceCreate,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(["CLIENT_OWNER", "CLIENT_EXECUTIVE", "CONSULTANT"]))
):
    """
    Create a new workspace inside the organization.
    """
    workspace = Workspace(
        organization_id=org_ctx.organization_id,
        name=workspace_in.name,
        description=workspace_in.description
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace
