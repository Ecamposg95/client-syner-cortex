from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, func, Index,
)
from app.database import Base


class Comment(Base):
    """A polymorphic comment attached to any commentable artifact (Task Pack §6).

    The target is identified by the (`object_type`, `object_id`) pair rather than
    a real foreign key, so a single table can hold comments for Reports,
    ToolRuns, RoadmapItems and Documents alike. `object_type` is a short string
    discriminator (e.g. "REPORT", "TOOLRUN", "ROADMAP_ITEM", "DOCUMENT") and
    `object_id` is the integer id of that artifact. A composite index on
    (object_type, object_id) makes "fetch all comments for this object" cheap.
    `organization_id` scopes every comment to its owning client org.
    """
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_object", "object_type", "object_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    # Polymorphic target discriminator + id (no ORM FK; kept deliberately simple).
    object_type = Column(String, nullable=False)
    object_id = Column(Integer, nullable=False, index=True)

    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
