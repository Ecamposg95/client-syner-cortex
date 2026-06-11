from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Date, Enum, Float
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base

# --- ENUMS ---
class EngagementStatus(enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class FindingCriticality(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class InitiativeStatus(enum.Enum):
    IDEA = "IDEA"
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class DecisionStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"

class RiskStatus(enum.Enum):
    OPEN = "OPEN"
    MITIGATING = "MITIGATING"
    MONITORING = "MONITORING"
    CLOSED = "CLOSED"

# --- CORE MODELS ---

class ConsultingEngagement(Base):
    __tablename__ = "clevel_engagements"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    title = Column(String, nullable=False)
    objective = Column(Text, nullable=True)
    status = Column(Enum(EngagementStatus), default=EngagementStatus.DRAFT)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Relationships
    findings = relationship("Finding", back_populates="engagement")
    initiatives = relationship("StrategicInitiative", back_populates="engagement")
    deliverables = relationship("Deliverable", back_populates="engagement")

class Finding(Base):
    __tablename__ = "clevel_findings"
    id = Column(Integer, primary_key=True, index=True)
    engagement_id = Column(Integer, ForeignKey("clevel_engagements.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    area = Column(String, nullable=True) # e.g. Operaciones, Finanzas
    criticality = Column(Enum(FindingCriticality), default=FindingCriticality.MEDIUM)
    impact = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    
    engagement = relationship("ConsultingEngagement", back_populates="findings")

class StrategicInitiative(Base):
    __tablename__ = "clevel_initiatives"
    id = Column(Integer, primary_key=True, index=True)
    engagement_id = Column(Integer, ForeignKey("clevel_engagements.id"), nullable=False)
    title = Column(String, nullable=False)
    objective = Column(Text, nullable=True)
    area = Column(String, nullable=True)
    status = Column(Enum(InitiativeStatus), default=InitiativeStatus.PROPOSED)
    priority = Column(String, nullable=True) # HIGH, MEDIUM, LOW
    estimated_budget = Column(Float, nullable=True)
    
    engagement = relationship("ConsultingEngagement", back_populates="initiatives")

class Deliverable(Base):
    __tablename__ = "clevel_deliverables"
    id = Column(Integer, primary_key=True, index=True)
    engagement_id = Column(Integer, ForeignKey("clevel_engagements.id"), nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=True) # e.g. Deck, Blueprint, Benchmark
    status = Column(String, default="DRAFT") # DRAFT, IN_REVIEW, DELIVERED, APPROVED
    file_url = Column(String, nullable=True)
    executive_summary = Column(Text, nullable=True)
    
    engagement = relationship("ConsultingEngagement", back_populates="deliverables")

class Risk(Base):
    __tablename__ = "clevel_risks"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=True) # Operativo, Tecnologico, etc.
    probability = Column(String, nullable=True) # HIGH, MEDIUM, LOW
    impact = Column(String, nullable=True) # HIGH, MEDIUM, LOW
    mitigation_plan = Column(Text, nullable=True)
    status = Column(Enum(RiskStatus), default=RiskStatus.OPEN)

class Decision(Base):
    __tablename__ = "clevel_decisions"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    title = Column(String, nullable=False)
    context = Column(Text, nullable=True)
    options = Column(Text, nullable=True)
    syner_recommendation = Column(Text, nullable=True)
    status = Column(Enum(DecisionStatus), default=DecisionStatus.PENDING)
    deadline = Column(Date, nullable=True)
