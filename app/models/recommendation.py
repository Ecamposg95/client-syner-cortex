from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Enum, DateTime, func,
)
import enum
from app.database import Base


# --- ENUMS (Task Pack §5) ---
class RecVisibility(enum.Enum):
    """Who may see a recommendation. INTERNAL is consultant-only; SHARED is
    visible to the client; EXECUTIVE_ONLY restricts to C-level; TASK_VISIBLE
    surfaces it alongside the task that operationalizes it."""
    INTERNAL = "INTERNAL"
    SHARED = "SHARED"
    EXECUTIVE_ONLY = "EXECUTIVE_ONLY"
    TASK_VISIBLE = "TASK_VISIBLE"


class Recommendation(Base):
    """A standalone recommendation (§6), distinct from toolkit.ToolRecommendation.
    Scoped to a workspace (and organization for cross-workspace queries), it
    captures an actionable suggestion along an impact/effort axis, with a
    visibility gate and an optional link to the roadmap item that delivers it."""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    dimension = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    visibility = Column(Enum(RecVisibility), default=RecVisibility.INTERNAL, nullable=False)

    impact = Column(String, nullable=True)
    effort = Column(String, nullable=True)

    linked_roadmap_item_id = Column(Integer, ForeignKey("roadmap_items.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
