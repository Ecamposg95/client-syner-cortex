from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.survey import CampaignStatus, SurveyResponse, Survey, SurveySection
from app.schemas.survey import (
    PublicSurveyView, PublicSection, PublicQuestion, PublicResponseSubmit,
)
from app.services.survey.service import SurveyService

router = APIRouter()


def _check_availability(campaign):
    """Raise HTTPException if the campaign is not open / within window."""
    if campaign.status != CampaignStatus.OPEN:
        raise HTTPException(status_code=403, detail="Esta encuesta no está disponible.")

    now = datetime.utcnow()
    if campaign.opens_at is not None and now < campaign.opens_at:
        raise HTTPException(status_code=403, detail="Esta encuesta aún no está abierta.")
    if campaign.closes_at is not None and now > campaign.closes_at:
        raise HTTPException(status_code=403, detail="Esta encuesta ya cerró.")


@router.get("/public/surveys/{token}", response_model=PublicSurveyView, tags=["public-surveys"])
def get_public_survey(token: str, db: Session = Depends(get_db)):
    campaign = SurveyService.get_public_view(db, token)
    if not campaign:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada.")

    _check_availability(campaign)

    survey = campaign.survey
    sections = []
    for section in sorted(survey.sections, key=lambda s: s.order or 0):
        questions = [
            PublicQuestion(
                id=q.id,
                order=q.order,
                text=q.text,
                question_type=q.question_type,
                options=q.options,
                is_required=q.is_required,
                scale_min=q.scale_min,
                scale_max=q.scale_max,
                scale_min_label=q.scale_min_label,
                scale_max_label=q.scale_max_label,
            )
            for q in sorted(section.questions, key=lambda x: x.order or 0)
        ]
        sections.append(PublicSection(
            id=section.id,
            title=section.title,
            order=section.order,
            questions=questions,
        ))

    return PublicSurveyView(
        campaign_id=campaign.id,
        title=survey.title,
        description=survey.description,
        is_anonymous=campaign.is_anonymous,
        collect_email=campaign.collect_email,
        sections=sections,
    )


@router.post("/public/surveys/{token}/responses", tags=["public-surveys"])
def submit_public_response(
    token: str,
    data: PublicResponseSubmit,
    request: Request,
    db: Session = Depends(get_db),
):
    campaign = SurveyService.get_public_view(db, token)
    if not campaign:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada.")

    _check_availability(campaign)

    # enforce max_responses
    if campaign.max_responses is not None:
        current = db.query(SurveyResponse).filter(
            SurveyResponse.campaign_id == campaign.id
        ).count()
        if current >= campaign.max_responses:
            raise HTTPException(status_code=403, detail="Se alcanzó el límite de respuestas.")

    # enforce email collection
    if campaign.collect_email and not data.respondent_email:
        raise HTTPException(status_code=422, detail="El correo electrónico es obligatorio.")

    meta = {
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }

    try:
        response = SurveyService.submit_response(db, campaign, data, meta)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return {"id": response.id, "message": "¡Gracias! Tu respuesta fue registrada."}
