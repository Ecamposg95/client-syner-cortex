from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
from app.models.survey import SurveyQuestionType, CampaignStatus


# ─────────────────────────── PUBLIC (no auth) ───────────────────────────
# Shapes returned to / accepted from anonymous respondents. Note these
# deliberately omit internal fields such as `diagnostic_use`.

class PublicQuestion(BaseModel):
    id: int
    order: int
    text: str
    question_type: SurveyQuestionType
    options: Optional[List[str]] = None
    is_required: bool = True
    scale_min: Optional[int] = None
    scale_max: Optional[int] = None
    scale_min_label: Optional[str] = None
    scale_max_label: Optional[str] = None

    class Config:
        from_attributes = True


class PublicSection(BaseModel):
    id: int
    title: str
    order: int
    questions: List[PublicQuestion] = []

    class Config:
        from_attributes = True


class PublicSurveyView(BaseModel):
    campaign_id: int
    title: str
    description: Optional[str] = None
    is_anonymous: bool
    collect_email: bool
    sections: List[PublicSection] = []


class PublicAnswerSubmit(BaseModel):
    question_id: int
    value_text: Optional[str] = None
    value_number: Optional[int] = None
    value_options: Optional[List[str]] = None


class PublicResponseSubmit(BaseModel):
    respondent_email: Optional[str] = None
    respondent_name: Optional[str] = None
    answers: List[PublicAnswerSubmit] = []


# ─────────────────────────── CREW (auth) ───────────────────────────

class QuestionCreate(BaseModel):
    order: int = 0
    text: str
    question_type: SurveyQuestionType
    options: Optional[List[str]] = None
    is_required: bool = True
    scale_min: Optional[int] = None
    scale_max: Optional[int] = None
    scale_min_label: Optional[str] = None
    scale_max_label: Optional[str] = None
    diagnostic_use: Optional[str] = None


class SectionCreate(BaseModel):
    title: str
    order: int = 0
    questions: List[QuestionCreate] = []


class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    sections: List[SectionCreate] = []


class SurveySummary(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_template: bool
    organization_id: Optional[int] = None
    created_at: datetime
    question_count: int = 0
    campaign_count: int = 0

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    name: str
    is_anonymous: bool = True
    collect_email: bool = False
    opens_at: Optional[datetime] = None
    closes_at: Optional[datetime] = None
    max_responses: Optional[int] = None
    workspace_id: Optional[int] = None


class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus


class CampaignResponse(BaseModel):
    id: int
    survey_id: int
    name: str
    public_token: str
    status: CampaignStatus
    is_anonymous: bool
    collect_email: bool
    opens_at: Optional[datetime] = None
    closes_at: Optional[datetime] = None
    max_responses: Optional[int] = None
    created_at: datetime
    response_count: int = 0
    # Convenience: relative public path the crew can copy/share (e.g. "/r/<token>")
    public_path: Optional[str] = None

    class Config:
        from_attributes = True


# Aggregated results are returned as a free-form dict per question, plus the
# triggered diagnostic readings. Defined loosely to keep the analytics flexible.
class CampaignResults(BaseModel):
    campaign_id: int
    survey_title: str
    response_count: int
    questions: List[Dict[str, Any]] = []          # per-question aggregation
    diagnostic_readings: List[Dict[str, Any]] = []  # triggered SurveyDiagnosticRule(s)
