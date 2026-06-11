from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
from app.models.toolkit import ToolRunStatus, Visibility

# --- Toolkits & Tools ---
class ConsultingToolkitBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True

class ConsultingToolkitCreate(ConsultingToolkitBase):
    pass

class ConsultingToolkitResponse(ConsultingToolkitBase):
    id: int

    class Config:
        from_attributes = True

class ConsultingToolBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class ConsultingToolCreate(ConsultingToolBase):
    toolkit_id: int

class ConsultingToolResponse(ConsultingToolBase):
    id: int
    toolkit_id: int

    class Config:
        from_attributes = True

# --- Tool Runs ---
class ToolRunCreate(BaseModel):
    tool_id: int
    workspace_id: Optional[int] = None

class ToolRunUpdateStatus(BaseModel):
    status: ToolRunStatus

class ToolRunResponse(BaseModel):
    id: int
    organization_id: int
    workspace_id: Optional[int]
    tool_id: int
    created_by: int
    status: ToolRunStatus
    visibility: Visibility
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Inputs & Outputs ---
class ToolInputCreate(BaseModel):
    key: str
    value: str

class ToolInputResponse(BaseModel):
    id: int
    run_id: int
    key: str
    value: Optional[str]
    uploaded_by: int

    class Config:
        from_attributes = True

class ToolOutputResponse(BaseModel):
    id: int
    run_id: int
    content_json: Optional[Dict[str, Any]]
    content_markdown: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True

# --- Recommendations ---
class ToolRecommendationCreate(BaseModel):
    title: str
    description: Optional[str] = None

class ToolRecommendationResponse(BaseModel):
    id: int
    run_id: int
    title: str
    description: Optional[str]
    is_converted_to_roadmap: bool
    roadmap_item_id: Optional[int]

    class Config:
        from_attributes = True

# --- Exports ---
class ToolExportResponse(BaseModel):
    id: int
    run_id: int
    format: str
    file_url: Optional[str]
    exported_at: datetime
    exported_by: int

    class Config:
        from_attributes = True
