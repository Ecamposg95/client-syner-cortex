from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Date, Enum, Float, JSON, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base

# --- ENUMS ---
class ToolRunStatus(enum.Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    AI_GENERATED = "AI_GENERATED"
    CONSULTANT_REVIEW = "CONSULTANT_REVIEW"
    APPROVED = "APPROVED"
    CLIENT_SHARED = "CLIENT_SHARED"
    ARCHIVED = "ARCHIVED"

class Visibility(enum.Enum):
    INTERNAL_ONLY = "INTERNAL_ONLY"
    CLIENT_SHARED = "CLIENT_SHARED"
    CLIENT_UPLOAD = "CLIENT_UPLOAD"
    DRAFT_INTERNAL = "DRAFT_INTERNAL"
    APPROVED = "APPROVED"
    CLIENT_VISIBLE = "CLIENT_VISIBLE"

# --- MODELS ---

class ConsultingToolkit(Base):
    __tablename__ = "toolkit_toolkits"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g. "Strategic Diagnosis Toolkit"
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    tools = relationship("ConsultingTool", back_populates="toolkit")

class ConsultingTool(Base):
    __tablename__ = "toolkit_tools"
    id = Column(Integer, primary_key=True, index=True)
    toolkit_id = Column(Integer, ForeignKey("toolkit_toolkits.id"), nullable=False)
    name = Column(String, nullable=False) # e.g. "FODA Ejecutivo"
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    toolkit = relationship("ConsultingToolkit", back_populates="tools")
    templates = relationship("ToolTemplate", back_populates="tool")
    runs = relationship("ToolRun", back_populates="tool")

class ToolTemplate(Base):
    __tablename__ = "toolkit_templates"
    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("toolkit_tools.id"), nullable=False)
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    json_schema_output = Column(JSON, nullable=True)
    version = Column(String, default="1.0")

    tool = relationship("ConsultingTool", back_populates="templates")

class ToolRun(Base):
    __tablename__ = "toolkit_runs"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    tool_id = Column(Integer, ForeignKey("toolkit_tools.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(Enum(ToolRunStatus), default=ToolRunStatus.DRAFT)
    visibility = Column(Enum(Visibility), default=Visibility.INTERNAL_ONLY)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tool = relationship("ConsultingTool", back_populates="runs")
    inputs = relationship("ToolInput", back_populates="run", cascade="all, delete-orphan")
    outputs = relationship("ToolOutput", back_populates="run", cascade="all, delete-orphan")
    recommendations = relationship("ToolRecommendation", back_populates="run", cascade="all, delete-orphan")
    exports = relationship("ToolExport", back_populates="run", cascade="all, delete-orphan")

class ToolInput(Base):
    __tablename__ = "toolkit_inputs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("toolkit_runs.id"), nullable=False)
    key = Column(String, nullable=False) # e.g. "fortalezas_detectadas"
    value = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    run = relationship("ToolRun", back_populates="inputs")

class ToolOutput(Base):
    __tablename__ = "toolkit_outputs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("toolkit_runs.id"), nullable=False)
    content_json = Column(JSON, nullable=True)
    content_markdown = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ToolRun", back_populates="outputs")
    evidence = relationship("ToolEvidence", back_populates="output", cascade="all, delete-orphan")

class ToolEvidence(Base):
    __tablename__ = "toolkit_evidence"
    id = Column(Integer, primary_key=True, index=True)
    output_id = Column(Integer, ForeignKey("toolkit_outputs.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    reference_text = Column(Text, nullable=True)
    link = Column(String, nullable=True)

    output = relationship("ToolOutput", back_populates="evidence")

class ToolRecommendation(Base):
    __tablename__ = "toolkit_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("toolkit_runs.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_converted_to_roadmap = Column(Boolean, default=False)
    roadmap_item_id = Column(Integer, nullable=True) # Linked to another module later

    run = relationship("ToolRun", back_populates="recommendations")

class ToolExport(Base):
    __tablename__ = "toolkit_exports"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("toolkit_runs.id"), nullable=False)
    format = Column(String, nullable=False) # 'MARKDOWN', 'PDF', 'DOCX'
    file_url = Column(String, nullable=True)
    exported_at = Column(DateTime, default=datetime.utcnow)
    exported_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    run = relationship("ToolRun", back_populates="exports")
