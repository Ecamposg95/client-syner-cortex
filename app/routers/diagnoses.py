from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Diagnosis, Workspace, OrganizationUser
from app.schemas.schemas import DiagnosisCreate, DiagnosisOut
from app.dependencies import get_current_org_id, get_organization_context, RoleChecker
from app.policy import Action
from app.policy.deps import get_principal, require_action
from app.policy.principal import Principal
from app.services.diagnosis_engine import generate_diagnosis_recommendations_and_roadmap

router = APIRouter(prefix="/diagnoses", tags=["diagnoses"])

# Diagnosis is NOT modelled as a policy ObjectType, so its client visibility is
# filtered by hand here. A Diagnosis carries the states INTERNAL_ONLY,
# DRAFT_INTERNAL, APPROVED, CLIENT_VISIBLE; of these ONLY CLIENT_VISIBLE may ever
# reach a CLIENT_USER. Everything else (including APPROVED, which is an internal
# sign-off state, not a client-share state) stays hidden. Being conservative:
# over-hiding is safe, over-exposing is a leak.
_CLIENT_VISIBLE_DIAGNOSIS_STATES = {"CLIENT_VISIBLE"}


def _client_can_see_diagnosis(principal: Principal, diag: Diagnosis) -> bool:
    """Crew/superadmin see every diagnosis in scope; a CLIENT_USER only sees a
    diagnosis in the CLIENT_VISIBLE state."""
    if principal.is_crew or principal.is_superadmin:
        return True
    return diag.visibility in _CLIENT_VISIBLE_DIAGNOSIS_STATES


@router.post("", response_model=DiagnosisOut, status_code=status.HTTP_201_CREATED)
def submit_diagnosis(
    workspace_id: int,
    diag_in: DiagnosisCreate,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    # Eje 2: RUN_TOOLS is the §8 lane for executing an analysis/generator. The
    # previous ad-hoc role list (CLIENT_OWNER/CLIENT_EXECUTIVE/CONSULTANT) is a
    # subset of the roles the matrix grants this action, so admitted callers keep
    # access while the gate now derives from §8.
    principal: Principal = Depends(require_action(Action.RUN_TOOLS)),
):
    """
    Submit a new 360-degree diagnosis questionnaire. Generates SWOT and execution roadmaps.
    """
    # Eje 1: workspace must belong to the active organization.
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    # Run the engine to process diagnosis and generate roadmap
    diagnosis = generate_diagnosis_recommendations_and_roadmap(
        db,
        workspace_id,
        org_id,
        principal.user_id,
        diag_in
    )

    return diagnosis

@router.get("/latest", response_model=Optional[DiagnosisOut])
def get_latest_workspace_diagnosis(
    workspace_id: int,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(get_principal),
):
    """
    Retrieve the latest diagnosis generated for the workspace.

    Eje 3 (manual): the previous version returned the most-recent diagnosis with
    NO visibility filter, leaking INTERNAL_ONLY/DRAFT_INTERNAL/APPROVED diagnoses
    to clients. Now, for a CLIENT_USER, only the latest CLIENT_VISIBLE diagnosis
    is returned; if the most recent diagnoses are all internal, the client gets
    None (never an internal one). Crew/superadmin see the true latest.
    """
    # Eje 1: workspace must belong to the active organization.
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    q = db.query(Diagnosis).filter(
        Diagnosis.workspace_id == workspace_id
    )
    # For clients, restrict to client-visible states at the query layer so the
    # "latest" we surface is the latest VISIBLE one, not the latest internal one.
    if not (principal.is_crew or principal.is_superadmin):
        q = q.filter(Diagnosis.visibility.in_(_CLIENT_VISIBLE_DIAGNOSIS_STATES))

    latest_diag = q.order_by(Diagnosis.created_at.desc()).first()

    return latest_diag

@router.get("/{diagnosis_id}", response_model=DiagnosisOut)
def get_diagnosis_by_id(
    diagnosis_id: int,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(get_principal),
):
    """
    Fetch details of a specific diagnosis.

    Eje 1 + Eje 3: the diagnosis must live in the active organization (404, never
    403, when it belongs to another org so existence is not disclosed across
    tenants), and a CLIENT_USER may only read it when it is CLIENT_VISIBLE — any
    internal state 404s. Crew/superadmin read any diagnosis in scope.
    """
    diag = db.query(Diagnosis).filter(
        Diagnosis.id == diagnosis_id,
        Diagnosis.organization_id == org_id
    ).first()
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnosis not found")

    if not _client_can_see_diagnosis(principal, diag):
        raise HTTPException(status_code=404, detail="Diagnosis not found")

    return diag
