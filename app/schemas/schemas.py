from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from app.config import MIN_PASSWORD_LENGTH


def _validate_password_strength(v: str) -> str:
    if v is None or len(v) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.")
    return v

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

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

class LoginRequest(BaseModel):
    """Dedicated login payload — only email + password (no strength validation)."""
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    is_superadmin: bool
    user_type: str
    must_change_password: bool = False
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
    organization_type: str
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
    role: str # SUPERADMIN, SYNER_ADMIN, SYNER_PARTNER, SYNER_CONSULTANT, SYNER_ANALYST, CLIENT_OWNER, CLIENT_MANAGER, CLIENT_VIEWER

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
    visibility: str
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
    visibility: str
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
    visibility: str
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
    visibility: str
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
    visibility: str
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
    visibility: str
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
