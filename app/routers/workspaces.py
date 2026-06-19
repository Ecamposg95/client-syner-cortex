from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Workspace, OrganizationUser
from app.schemas.schemas import WorkspaceCreate, WorkspaceOut
from app.dependencies import get_organization_context, get_current_org_id
from app.policy import Action
from app.policy.deps import require_action

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("", response_model=List[WorkspaceOut])
def list_workspaces(
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    List all workspaces for the organization.
    """
    # Listing stays purely org-scoped (Eje 1): any validated member of the org
    # — crew or client — may enumerate the org's workspaces. get_organization_context
    # enforces membership; no §8 management capability is required to read.
    workspaces = db.query(Workspace).filter(Workspace.organization_id == org_ctx.organization_id).all()
    return workspaces

@router.post("", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace_in: WorkspaceCreate,
    db: Session = Depends(get_db),
    # §8: CREATE_WORKSPACE is ALLOW only for crew (SYNER_ADMIN/PARTNER/CONSULTANT).
    # require_action gates ejes 1+2 against the X-Organization-ID header; clients
    # (CLIENT_OWNER/EXECUTIVE/…) are no longer permitted to create workspaces.
    _principal=Depends(require_action(Action.CREATE_WORKSPACE)),
    # Validated org id for the new workspace (membership-checked, Eje 1). Kept as a
    # separate dep because require_action returns a Principal, not the org id.
    organization_id: int = Depends(get_current_org_id),
):
    """
    Create a new workspace inside the organization.
    """
    workspace = Workspace(
        organization_id=organization_id,
        name=workspace_in.name,
        description=workspace_in.description
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace
