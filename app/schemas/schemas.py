from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date

# ----------------- TOKEN SCHEMAS -----------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

# ----------------- USER SCHEMAS -----------------
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    is_superadmin: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- ORG SCHEMAS -----------------
class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationOut(OrganizationBase):
    id: int
    slug: str
    created_at: datetime

    class Config:
        from_attributes = True

class OrganizationUserOut(BaseModel):
    id: int
    organization_id: int
    user_id: int
    role: str
    organization: OrganizationOut

    class Config:
        from_attributes = True

class OrganizationAddUser(BaseModel):
    email: EmailStr
    role: str # SUPERADMIN, SYNER_ADMIN, CONSULTANT, CLIENT_OWNER, CLIENT_EXECUTIVE, CLIENT_MANAGER, CLIENT_VIEWER

# ----------------- WORKSPACE SCHEMAS -----------------
class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceOut(WorkspaceBase):
    id: int
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- DOCUMENT SCHEMAS -----------------
class DocumentOut(BaseModel):
    id: int
    workspace_id: int
    organization_id: int
    name: str
    file_type: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- CHAT SCHEMAS -----------------
class ChatMessageBase(BaseModel):
    content: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    sender: str # user or assistant
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    title: str

class ChatSessionOut(BaseModel):
    id: int
    workspace_id: int
    organization_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- DIAGNOSIS SCHEMAS -----------------
class DiagnosisDimensionAnswer(BaseModel):
    name: str # Ventas, Operaciones, Administracion, RH, Tecnologia
    rating: int = Field(..., ge=1, le=5)
    findings: str
    challenges: str # what challenges they face

class DiagnosisCreate(BaseModel):
    dimensions: List[DiagnosisDimensionAnswer]

class DiagnosisDimensionOut(BaseModel):
    id: int
    diagnosis_id: int
    name: str
    rating: int
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    swot_analysis: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class DiagnosisOut(BaseModel):
    id: int
    workspace_id: int
    organization_id: int
    status: str
    created_at: datetime
    dimensions: List[DiagnosisDimensionOut]

    class Config:
        from_attributes = True

# ----------------- ROADMAP SCHEMAS -----------------
class RoadmapItemUpdate(BaseModel):
    status: Optional[str] = None # TODO, IN_PROGRESS, DONE
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None

class RoadmapItemOut(BaseModel):
    id: int
    roadmap_id: int
    title: str
    description: Optional[str] = None
    dimension: str
    phase: int # 30, 60, 90
    status: str
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RoadmapOut(BaseModel):
    id: int
    workspace_id: int
    organization_id: int
    diagnosis_id: int
    created_at: datetime
    items: List[RoadmapItemOut]

    class Config:
        from_attributes = True

# ----------------- AUDIT SCHEMAS -----------------
class AuditLogOut(BaseModel):
    id: int
    organization_id: Optional[int] = None
    user_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
