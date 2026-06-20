"""Pydantic v2 schemas for the superadmin platform-configuration layer
(`AppSetting`). Settings are typed key-value rows; secrets are masked by the
router before serialization, so `value` here may already be `"****"`."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AppSettingUpsert(BaseModel):
    """Payload to create-or-update a setting by key. `key` is taken from the path
    on PUT but kept here so the schema is also usable for bulk writes."""
    key: str
    value: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None


class AppSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
