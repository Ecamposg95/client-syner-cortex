from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PlaybookCreate(BaseModel):
    title: str
    category: Optional[str] = None
    content: str = ""
    tags: Optional[List[str]] = None
    organization_id: Optional[int] = None  # NULL => firm-global library entry
    visibility: str = "INTERNAL_ONLY"


class PlaybookUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    organization_id: Optional[int] = None
    visibility: Optional[str] = None


class PlaybookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: Optional[int]
    created_by: Optional[int]
    title: str
    category: Optional[str]
    content: str
    tags: Optional[List[str]]
    visibility: str
    created_at: datetime
    updated_at: datetime
