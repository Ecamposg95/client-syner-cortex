from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Enum, JSON, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base


# --- ENUMS ---
class SurveyQuestionType(enum.Enum):
    SINGLE_CHOICE = "SINGLE_CHOICE"   # Opción múltiple
    MULTI_CHOICE = "MULTI_CHOICE"     # Casillas de verificación
    LINEAR_SCALE = "LINEAR_SCALE"     # Escala lineal 1-5
    OPEN_TEXT = "OPEN_TEXT"           # Respuesta abierta corta


class CampaignStatus(enum.Enum):
    DRAFT = "DRAFT"     # Aún no publicada
    OPEN = "OPEN"       # Aceptando respuestas vía URL pública
    CLOSED = "CLOSED"   # Cerrada, ya no acepta respuestas


# --- SURVEY DEFINITION ---

class Survey(Base):
    """Reusable survey definition. Can be a template (is_template=True) or an
    organization-owned instrument cloned from a template."""
    __tablename__ = "survey_surveys"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_template = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sections = relationship(
        "SurveySection", back_populates="survey",
        cascade="all, delete-orphan", order_by="SurveySection.order"
    )
    campaigns = relationship("SurveyCampaign", back_populates="survey")
    diagnostic_rules = relationship(
        "SurveyDiagnosticRule", back_populates="survey",
        cascade="all, delete-orphan"
    )


class SurveySection(Base):
    __tablename__ = "survey_sections"
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("survey_surveys.id"), nullable=False)
    title = Column(String, nullable=False)
    order = Column(Integer, default=0)

    survey = relationship("Survey", back_populates="sections")
    questions = relationship(
        "SurveyQuestion", back_populates="section",
        cascade="all, delete-orphan", order_by="SurveyQuestion.order"
    )


class SurveyQuestion(Base):
    __tablename__ = "survey_questions"
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("survey_sections.id"), nullable=False)
    order = Column(Integer, default=0)
    text = Column(Text, nullable=False)
    question_type = Column(Enum(SurveyQuestionType), nullable=False)
    options = Column(JSON, nullable=True)            # list[str] for choice questions
    is_required = Column(Boolean, default=True)
    # Linear scale config
    scale_min = Column(Integer, nullable=True)
    scale_max = Column(Integer, nullable=True)
    scale_min_label = Column(String, nullable=True)
    scale_max_label = Column(String, nullable=True)
    # Internal: how the Syner crew uses this answer in diagnosis (not shown publicly)
    diagnostic_use = Column(Text, nullable=True)

    section = relationship("SurveySection", back_populates="questions")
    answers = relationship("SurveyAnswer", back_populates="question")


class SurveyDiagnosticRule(Base):
    """Rule-based "Lectura Diagnóstica": pattern -> suggested classroom/consulting
    adjustment. Mirrors the 'Lectura Diagnóstico' sheet of the source matrix."""
    __tablename__ = "survey_diagnostic_rules"
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("survey_surveys.id"), nullable=False)
    pattern = Column(String, nullable=False)         # "Si aparece este patrón"
    suggestion = Column(Text, nullable=False)        # "Ajuste sugerido en clase"
    # Optional machine condition used by SurveyDiagnosticService to auto-trigger.
    # Free-form JSON, e.g. {"question_order": 15, "op": ">=", "value": 4}
    condition = Column(JSON, nullable=True)

    survey = relationship("Survey", back_populates="diagnostic_rules")


# --- DISTRIBUTION & RESPONSES ---

class SurveyCampaign(Base):
    """A distributable instance of a Survey, exposed through a public token URL."""
    __tablename__ = "survey_campaigns"
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("survey_surveys.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    name = Column(String, nullable=False)
    public_token = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    is_anonymous = Column(Boolean, default=True)
    collect_email = Column(Boolean, default=False)
    opens_at = Column(DateTime, nullable=True)
    closes_at = Column(DateTime, nullable=True)
    max_responses = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    survey = relationship("Survey", back_populates="campaigns")
    responses = relationship(
        "SurveyResponse", back_populates="campaign",
        cascade="all, delete-orphan"
    )


class SurveyResponse(Base):
    __tablename__ = "survey_responses"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("survey_campaigns.id"), nullable=False)
    respondent_email = Column(String, nullable=True)
    respondent_name = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)               # {"ip": ..., "user_agent": ...}
    visibility = Column(String, default="CLIENT_UPLOAD")
    submitted_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("SurveyCampaign", back_populates="responses")
    answers = relationship(
        "SurveyAnswer", back_populates="response",
        cascade="all, delete-orphan"
    )


class SurveyAnswer(Base):
    __tablename__ = "survey_answers"
    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("survey_responses.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("survey_questions.id"), nullable=False)
    value_text = Column(Text, nullable=True)         # OPEN_TEXT
    value_number = Column(Integer, nullable=True)    # LINEAR_SCALE
    value_options = Column(JSON, nullable=True)      # list[str] SINGLE/MULTI choice

    response = relationship("SurveyResponse", back_populates="answers")
    question = relationship("SurveyQuestion", back_populates="answers")
