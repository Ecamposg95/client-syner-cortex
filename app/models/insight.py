from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Float, Boolean, DateTime, func
import enum
from app.database import Base


# --- ENUMS ---
class InsightImpact(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class InsightEffort(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class InsightStatus(enum.Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class InsightSource(enum.Enum):
    FINDING = "FINDING"
    RISK = "RISK"
    DIAGNOSIS = "DIAGNOSIS"
    MANUAL = "MANUAL"


class Insight(Base):
    """Cortex Insights — prioritized recommendations distilled from the org's
    findings, risks and diagnosis. Each insight sits on an impact/effort matrix
    (quadrant) and carries a priority score so the highest-leverage actions rank
    first. `source_type`/`source_ref` record provenance and let the generator
    dedupe on re-run."""
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # business area, e.g. Operaciones, Finanzas

    impact = Column(Enum(InsightImpact), default=InsightImpact.MEDIUM, nullable=False)
    effort = Column(Enum(InsightEffort), default=InsightEffort.MEDIUM, nullable=False)
    priority_score = Column(Float, default=0.0, nullable=False)
    quadrant = Column(String, nullable=True)  # QUICK_WIN, MAJOR_PROJECT, INCREMENTAL, LOW_PRIORITY

    status = Column(Enum(InsightStatus), default=InsightStatus.NEW, nullable=False)
    is_critical_alarm = Column(Boolean, default=False, nullable=False)
    recommended_action = Column(Text, nullable=True)

    # Provenance — links the insight back to its originating artifact.
    source_type = Column(Enum(InsightSource), default=InsightSource.MANUAL, nullable=False)
    source_ref = Column(Integer, nullable=True)  # id of the originating finding/risk/dimension

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
