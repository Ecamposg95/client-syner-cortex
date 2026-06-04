from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Diagnosis, Workspace, OrganizationUser
from app.schemas.schemas import DiagnosisCreate, DiagnosisOut
from app.dependencies import get_organization_context, RoleChecker
from app.services.diagnosis_engine import generate_diagnosis_recommendations_and_roadmap

router = APIRouter(prefix="/diagnoses", tags=["diagnoses"])

@router.post("", response_model=DiagnosisOut, status_code=status.HTTP_201_CREATED)
def submit_diagnosis(
    workspace_id: int,
    diag_in: DiagnosisCreate,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(["CLIENT_OWNER", "CLIENT_EXECUTIVE", "CONSULTANT"]))
):
    """
    Submit a new 360-degree diagnosis questionnaire. Generates SWOT and execution roadmaps.
    """
    # Verify workspace belongs to organization
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    # Run the engine to process diagnosis and generate roadmap
    diagnosis = generate_diagnosis_recommendations_and_roadmap(
        db,
        workspace_id,
        org_ctx.organization_id,
        org_ctx.user_id,
        diag_in
    )
    
    return diagnosis

@router.get("/latest", response_model=Optional[DiagnosisOut])
def get_latest_workspace_diagnosis(
    workspace_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    Retrieve the latest diagnosis generated for the workspace.
    """
    # Verify workspace belongs to organization
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    latest_diag = db.query(Diagnosis).filter(
        Diagnosis.workspace_id == workspace_id
    ).order_by(Diagnosis.created_at.desc()).first()
    
    return latest_diag

@router.get("/{diagnosis_id}", response_model=DiagnosisOut)
def get_diagnosis_by_id(
    diagnosis_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    Fetch details of a specific diagnosis.
    """
    diag = db.query(Diagnosis).filter(
        Diagnosis.id == diagnosis_id,
        Diagnosis.organization_id == org_ctx.organization_id
    ).first()
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
        
    return diag
