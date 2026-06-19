from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime
from app.models.recommendation import RecVisibility


class RecommendationCreate(BaseModel):
    workspace_id: int
    organization_id: int
    dimension: Optional[str] = None
    text: str
    visibility: RecVisibility = RecVisibility.INTERNAL
    impact: Optional[str] = None
    effort: Optional[str] = None
    linked_roadmap_item_id: Optional[int] = None


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    organization_id: int
    dimension: Optional[str] = None
    text: str
    visibility: RecVisibility
    impact: Optional[str] = None
    effort: Optional[str] = None
    linked_roadmap_item_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("visibility")
    def _ser_visibility(self, v: RecVisibility) -> str:
        return v.value
