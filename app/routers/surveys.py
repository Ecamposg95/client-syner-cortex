from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_syner_crew
from app.models.survey import Survey, SurveySection, SurveyCampaign, SurveyResponse
from app.schemas.survey import (
    SurveyCreate, SurveySummary, CampaignCreate, CampaignResponse,
    CampaignStatusUpdate,
)
from app.services.survey.service import SurveyService, SurveyDiagnosticService

router = APIRouter()


def _optional_org_id(
    x_organization_id: Optional[int] = Header(None, alias="X-Organization-ID")
) -> Optional[int]:
    """Organization id from header, optional-friendly for crew listing."""
    return x_organization_id


def _question_count(survey: Survey) -> int:
    return sum(len(section.questions) for section in survey.sections)


def _survey_summary(survey: Survey) -> dict:
    return {
        "id": survey.id,
        "title": survey.title,
        "description": survey.description,
        "is_template": survey.is_template,
        "organization_id": survey.organization_id,
        "created_at": survey.created_at,
        "question_count": _question_count(survey),
        "campaign_count": len(survey.campaigns),
    }


def _campaign_response(campaign: SurveyCampaign, db: Session) -> dict:
    response_count = db.query(SurveyResponse).filter(
        SurveyResponse.campaign_id == campaign.id
    ).count()
    return {
        "id": campaign.id,
        "survey_id": campaign.survey_id,
        "name": campaign.name,
        "public_token": campaign.public_token,
        "status": campaign.status,
        "is_anonymous": campaign.is_anonymous,
        "collect_email": campaign.collect_email,
        "opens_at": campaign.opens_at,
        "closes_at": campaign.closes_at,
        "max_responses": campaign.max_responses,
        "created_at": campaign.created_at,
        "response_count": response_count,
        "public_path": f"/r/{campaign.public_token}",
    }


# ─── SURVEYS ───────────────────────────────────────────────────────

@router.get("/surveys", response_model=List[SurveySummary], tags=["surveys"])
def list_surveys(
    db: Session = Depends(get_db),
    org_id: Optional[int] = Depends(_optional_org_id),
    crew=Depends(get_current_syner_crew),
):
    surveys = SurveyService.list_surveys(db, org_id)
    return [_survey_summary(s) for s in surveys]


@router.post("/surveys", response_model=SurveySummary, tags=["surveys"])
def create_survey(
    data: SurveyCreate,
    db: Session = Depends(get_db),
    org_id: Optional[int] = Depends(_optional_org_id),
    crew=Depends(get_current_syner_crew),
):
    survey = SurveyService.create_survey(db, data, org_id, crew.id)
    return _survey_summary(survey)


@router.post("/surveys/from-template/{template_id}", response_model=SurveySummary, tags=["surveys"])
def clone_template(
    template_id: int,
    db: Session = Depends(get_db),
    org_id: Optional[int] = Depends(_optional_org_id),
    crew=Depends(get_current_syner_crew),
):
    survey = SurveyService.clone_template(db, template_id, org_id, crew.id)
    if not survey:
        raise HTTPException(status_code=404, detail="Template not found")
    return _survey_summary(survey)


@router.get("/surveys/{survey_id}", tags=["surveys"])
def get_survey_detail(
    survey_id: int,
    db: Session = Depends(get_db),
    crew=Depends(get_current_syner_crew),
):
    survey = (
        db.query(Survey)
        .options(joinedload(Survey.sections).joinedload(SurveySection.questions))
        .filter(Survey.id == survey_id)
        .first()
    )
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return {
        "id": survey.id,
        "title": survey.title,
        "description": survey.description,
        "is_template": survey.is_template,
        "organization_id": survey.organization_id,
        "created_at": survey.created_at,
        "sections": [
            {
                "id": section.id,
                "title": section.title,
                "order": section.order,
                "questions": [
                    {
                        "id": q.id,
                        "order": q.order,
                        "text": q.text,
                        "question_type": q.question_type.value,
                        "options": q.options,
                        "is_required": q.is_required,
                        "scale_min": q.scale_min,
                        "scale_max": q.scale_max,
                        "scale_min_label": q.scale_min_label,
                        "scale_max_label": q.scale_max_label,
                        "diagnostic_use": q.diagnostic_use,
                    }
                    for q in sorted(section.questions, key=lambda x: x.order or 0)
                ],
            }
            for section in sorted(survey.sections, key=lambda s: s.order or 0)
        ],
    }


# ─── CAMPAIGNS ─────────────────────────────────────────────────────

@router.post("/surveys/{survey_id}/campaigns", response_model=CampaignResponse, tags=["surveys"])
def create_campaign(
    survey_id: int,
    data: CampaignCreate,
    db: Session = Depends(get_db),
    org_id: Optional[int] = Depends(_optional_org_id),
    crew=Depends(get_current_syner_crew),
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    campaign = SurveyService.create_campaign(db, survey_id, data, org_id, crew.id)
    return _campaign_response(campaign, db)


@router.get("/campaigns", response_model=List[CampaignResponse], tags=["surveys"])
def list_campaigns(
    db: Session = Depends(get_db),
    org_id: Optional[int] = Depends(_optional_org_id),
    crew=Depends(get_current_syner_crew),
):
    query = db.query(SurveyCampaign)
    if org_id is not None:
        query = query.filter(SurveyCampaign.organization_id == org_id)
    campaigns = query.all()
    return [_campaign_response(c, db) for c in campaigns]


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse, tags=["surveys"])
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    crew=Depends(get_current_syner_crew),
):
    campaign = db.query(SurveyCampaign).filter(SurveyCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _campaign_response(campaign, db)


@router.patch("/campaigns/{campaign_id}/status", response_model=CampaignResponse, tags=["surveys"])
def update_campaign_status(
    campaign_id: int,
    data: CampaignStatusUpdate,
    db: Session = Depends(get_db),
    crew=Depends(get_current_syner_crew),
):
    campaign = db.query(SurveyCampaign).filter(SurveyCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = data.status
    db.commit()
    db.refresh(campaign)
    return _campaign_response(campaign, db)


@router.get("/campaigns/{campaign_id}/results", tags=["surveys"])
def get_campaign_results(
    campaign_id: int,
    db: Session = Depends(get_db),
    crew=Depends(get_current_syner_crew),
):
    results = SurveyService.aggregate_results(db, campaign_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = db.query(SurveyCampaign).filter(SurveyCampaign.id == campaign_id).first()
    readings = SurveyDiagnosticService.evaluate(
        db,
        campaign.survey_id,
        results["questions"],
        results["response_count"],
    )
    results["diagnostic_readings"] = readings
    return results
