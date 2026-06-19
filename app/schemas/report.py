from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional, Any, Dict
from datetime import datetime
from app.models.report import ReportStatus


class ReportCreate(BaseModel):
    organization_id: int
    workspace_id: Optional[int] = None
    created_by: Optional[int] = None
    title: str
    report_type: Optional[str] = None
    status: ReportStatus = ReportStatus.DRAFT_INTERNAL
    visibility: str = "DRAFT_INTERNAL"
    content: Optional[Dict[str, Any]] = None


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    workspace_id: Optional[int] = None
    created_by: Optional[int] = None
    title: str
    report_type: Optional[str] = None
    status: ReportStatus
    visibility: str
    content: Optional[Dict[str, Any]] = None
    approved_by: Optional[int] = None
    shared_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("status")
    def _ser_status(self, v: ReportStatus) -> str:
        return v.value
