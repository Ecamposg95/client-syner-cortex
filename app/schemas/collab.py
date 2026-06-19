"""Pydantic v2 schemas for the collaboration data layer (Task Pack §6):
workspace membership (`WorkspaceUser`) and polymorphic `Comment`s.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ─────────────────────────── WorkspaceUser ───────────────────────────
class WorkspaceUserCreate(BaseModel):
    workspace_id: int
    user_id: int
    workspace_role: str
    visibility_scope: Optional[str] = None


class WorkspaceUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    user_id: int
    workspace_role: str
    visibility_scope: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────── Comment ─────────────────────────────
class CommentCreate(BaseModel):
    object_type: str
    object_id: int
    organization_id: int
    author_id: int
    content: str


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    object_type: str
    object_id: int
    organization_id: int
    author_id: int
    content: str
    created_at: datetime
    updated_at: datetime
