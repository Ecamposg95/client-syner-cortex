from sqlalchemy import (
    Column, Integer, String, ForeignKey, Enum, JSON, DateTime, func,
)
import enum
from app.database import Base


# --- ENUMS (Task Pack §5) ---
class ReportStatus(enum.Enum):
    """Lifecycle of a consultant-authored report. Starts as an internal draft,
    moves through consultant review and approval, and is only ever exposed to
    the client once it reaches CLIENT_SHARED. ARCHIVED retires it from the
    active workspace without deleting the record."""
    DRAFT_INTERNAL = "DRAFT_INTERNAL"
    CONSULTANT_REVIEW = "CONSULTANT_REVIEW"
    APPROVED = "APPROVED"
    CLIENT_SHARED = "CLIENT_SHARED"
    ARCHIVED = "ARCHIVED"


class Report(Base):
    """A standalone consulting report (§6). Scoped to an organization and
    optionally to a workspace, it carries free-form JSON content plus the
    review/approval/sharing metadata that drives the DRAFT_INTERNAL →
    CLIENT_SHARED visibility lifecycle."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    title = Column(String, nullable=False)
    report_type = Column(String, nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT_INTERNAL, nullable=False)
    visibility = Column(String, nullable=False, default="DRAFT_INTERNAL")
    content = Column(JSON, nullable=True)

    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    shared_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
