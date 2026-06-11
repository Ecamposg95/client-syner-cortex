from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import datetime

from app.database import get_db
from app.dependencies import get_current_org_id, get_current_user, RoleChecker
from app.models.models import OrganizationUser
from app.models.clevel import (
    ConsultingEngagement, Finding, StrategicInitiative,
    Deliverable, Risk, Decision, DecisionStatus
)

router = APIRouter()

# --- Pydantic Schemas ---

class EngagementResponse(BaseModel):
    id: int
    title: str
    objective: str | None
    status: str
    start_date: datetime.date | None
    end_date: datetime.date | None

    class Config:
        orm_mode = True

class FindingResponse(BaseModel):
    id: int
    engagement_id: int
    title: str
    description: str | None
    area: str | None
    criticality: str
    impact: str | None
    recommendation: str | None

    class Config:
        orm_mode = True

class InitiativeResponse(BaseModel):
    id: int
    engagement_id: int
    title: str
    objective: str | None
    area: str | None
    status: str
    priority: str | None
    estimated_budget: float | None

    class Config:
        orm_mode = True

class DeliverableResponse(BaseModel):
    id: int
    engagement_id: int
    title: str
    type: str | None
    status: str
    executive_summary: str | None

    class Config:
        orm_mode = True

class RiskResponse(BaseModel):
    id: int
    description: str
    category: str | None
    probability: str | None
    impact: str | None
    mitigation_plan: str | None
    status: str

    class Config:
        orm_mode = True

class DecisionResponse(BaseModel):
    id: int
    title: str
    context: str | None
    options: str | None
    syner_recommendation: str | None
    status: str
    deadline: datetime.date | None

    class Config:
        orm_mode = True

# --- Endpoints ---

@router.get("/clevel/engagements", response_model=List[EngagementResponse], tags=["clevel"])
def get_engagements(org_id: int = Depends(get_current_org_id), db: Session = Depends(get_db)):
    return db.query(ConsultingEngagement).filter(ConsultingEngagement.organization_id == org_id).all()

@router.get("/clevel/engagements/{engagement_id}/findings", response_model=List[FindingResponse], tags=["clevel"])
def get_findings(engagement_id: int, org_id: int = Depends(get_current_org_id), db: Session = Depends(get_db)):
    eng = db.query(ConsultingEngagement).filter(ConsultingEngagement.id == engagement_id, ConsultingEngagement.organization_id == org_id).first()
    if not eng:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return db.query(Finding).filter(Finding.engagement_id == engagement_id).all()

@router.get("/clevel/engagements/{engagement_id}/initiatives", response_model=List[InitiativeResponse], tags=["clevel"])
def get_initiatives(engagement_id: int, org_id: int = Depends(get_current_org_id), db: Session = Depends(get_db)):
    eng = db.query(ConsultingEngagement).filter(ConsultingEngagement.id == engagement_id, ConsultingEngagement.organization_id == org_id).first()
    if not eng:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return db.query(StrategicInitiative).filter(StrategicInitiative.engagement_id == engagement_id).all()

@router.get("/clevel/engagements/{engagement_id}/deliverables", response_model=List[DeliverableResponse], tags=["clevel"])
def get_deliverables(engagement_id: int, org_id: int = Depends(get_current_org_id), db: Session = Depends(get_db)):
    eng = db.query(ConsultingEngagement).filter(ConsultingEngagement.id == engagement_id, ConsultingEngagement.organization_id == org_id).first()
    if not eng:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return db.query(Deliverable).filter(Deliverable.engagement_id == engagement_id).all()

@router.get("/clevel/risks", response_model=List[RiskResponse], tags=["clevel"])
def get_risks(org_id: int = Depends(get_current_org_id), db: Session = Depends(get_db)):
    return db.query(Risk).filter(Risk.organization_id == org_id).all()

@router.get("/clevel/decisions", response_model=List[DecisionResponse], tags=["clevel"])
def get_decisions(org_id: int = Depends(get_current_org_id), db: Session = Depends(get_db)):
    return db.query(Decision).filter(Decision.organization_id == org_id).all()


class DecisionUpdate(BaseModel):
    status: str  # PENDING, APPROVED, REJECTED, DEFERRED, NEEDS_MORE_INFO


# Client action: a client owner/manager (or crew) can resolve a pending decision.
_DECISION_ROLES = ["CLIENT_OWNER", "CLIENT_EXECUTIVE", "CLIENT_MANAGER",
                   "SYNER_PARTNER", "SYNER_CONSULTANT"]


@router.patch("/clevel/decisions/{decision_id}", response_model=DecisionResponse, tags=["clevel"])
def update_decision(
    decision_id: int,
    payload: DecisionUpdate,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(_DECISION_ROLES)),
):
    valid = {s.value for s in DecisionStatus}
    if payload.status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {sorted(valid)}")
    decision = db.query(Decision).filter(
        Decision.id == decision_id,
        Decision.organization_id == org_ctx.organization_id,
    ).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    decision.status = DecisionStatus(payload.status)
    db.commit()
    db.refresh(decision)
    return decision
