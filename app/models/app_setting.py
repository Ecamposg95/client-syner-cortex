from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, func,
)
from app.database import Base


class AppSetting(Base):
    """Platform-wide configuration as typed key-value rows, editable only by a
    superadmin (NOT org-scoped). Each row is a single setting (e.g. AI_PROVIDER,
    RAG_TOP_K, MAX_UPLOAD_MB) optionally grouped by `category` ("AI"/"RAG"/
    "LIMITS"/...). `value` is stored as text and parsed/coerced by callers; the
    effective configuration is the sensible defaults overlaid with these rows.
    `updated_by` records the superadmin who last wrote the setting."""
    __tablename__ = "app_settings"
    __table_args__ = (UniqueConstraint("key", name="uq_app_settings_key"),)

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # e.g. "AI", "RAG", "LIMITS", "INTEGRATIONS"
    description = Column(String, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
