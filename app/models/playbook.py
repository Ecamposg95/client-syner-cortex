from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, func
from app.database import Base


class Playbook(Base):
    """Internal Syner Playbooks — the firm's private library of methodologies,
    frameworks and operating procedures. These are CREW-ONLY artifacts: a client
    must NEVER see a playbook through any endpoint (visibility defaults to
    INTERNAL_ONLY and every route is gated by get_current_syner_crew).

    `organization_id` is nullable on purpose: a NULL row is a firm-global
    playbook shared across the whole crew; a non-NULL row scopes the playbook to
    a particular org's engagement. `created_by` records authorship.
    """
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )  # NULL => firm-global library entry
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title = Column(String, nullable=False)
    category = Column(String, nullable=True)  # e.g. Diagnóstico, Ventas, Operaciones
    content = Column(Text, nullable=False, default="")
    tags = Column(JSON, nullable=True)  # list[str] of free-form labels

    visibility = Column(String, nullable=False, default="INTERNAL_ONLY")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
