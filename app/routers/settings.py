"""Superadmin platform configuration (`/settings`).

Platform-wide settings (IA/RAG/limits/models/integrations) live as typed
key-value `AppSetting` rows. These are NOT org-scoped: they govern the whole
platform, so every endpoint here is SUPERADMIN-ONLY — we gate on
`current_user.is_superadmin` rather than the org-policy `require_action`.

Secrets are never echoed back: any setting whose key looks like a credential
(contains KEY / SECRET / TOKEN / PASSWORD) has its value masked to "****" in
responses, so reading the config can't exfiltrate API keys.

The orchestrator mounts this router under the `/api` prefix.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.models import User
from app.models.app_setting import AppSetting
from app.schemas.app_setting import AppSettingOut, AppSettingUpsert

router = APIRouter()

MASK = "****"
_SECRET_HINTS = ("KEY", "SECRET", "TOKEN", "PASSWORD")

# Sensible platform defaults. The effective config = these overlaid with whatever
# the superadmin has persisted in app_settings. Kept intentionally small.
DEFAULT_SETTINGS = {
    "AI_PROVIDER": {"value": "anthropic", "category": "AI",
                    "description": "Proveedor de modelos de IA por defecto"},
    "AI_MODEL": {"value": "claude-sonnet-4-5", "category": "AI",
                 "description": "Modelo de IA por defecto para generación"},
    "AI_TEMPERATURE": {"value": "0.2", "category": "AI",
                       "description": "Temperatura de muestreo (0-2)"},
    "RAG_TOP_K": {"value": "5", "category": "RAG",
                  "description": "Número de fragmentos recuperados por consulta"},
    "RAG_CHUNK_SIZE": {"value": "1000", "category": "RAG",
                       "description": "Tamaño de chunk (caracteres) para indexar documentos"},
    "MAX_UPLOAD_MB": {"value": "25", "category": "LIMITS",
                      "description": "Tamaño máximo de archivo subido (MB)"},
    "MAX_DOCS_PER_WORKSPACE": {"value": "500", "category": "LIMITS",
                               "description": "Documentos máximos por workspace"},
}


def _is_secret(key: str) -> bool:
    k = (key or "").upper()
    return any(h in k for h in _SECRET_HINTS)


def _mask_value(key: str, value: Optional[str]) -> Optional[str]:
    """Mask the value of secret-looking keys (only when a value is actually set)."""
    if value not in (None, "") and _is_secret(key):
        return MASK
    return value


def _serialize(s: AppSetting) -> AppSettingOut:
    return AppSettingOut(
        id=s.id,
        key=s.key,
        value=_mask_value(s.key, s.value),
        category=s.category,
        description=s.description,
        updated_by=s.updated_by,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def require_superadmin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Platform settings are global, not org-scoped: only superadmins may touch
    them. Anyone else (incl. SYNER_CREW and CLIENT_USER) gets a 403."""
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return current_user


@router.get("/settings", response_model=List[AppSettingOut], tags=["settings"])
def list_settings(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_superadmin),
):
    """List every stored platform setting (optionally filtered by category).
    Secret values are masked. Group by `category` on the client."""
    q = db.query(AppSetting)
    if category:
        q = q.filter(AppSetting.category == category)
    rows = q.order_by(AppSetting.category, AppSetting.key).all()
    return [_serialize(r) for r in rows]


@router.put("/settings/{key}", response_model=AppSettingOut, tags=["settings"])
def upsert_setting(
    key: str,
    payload: AppSettingUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(require_superadmin),
):
    """Create or update a setting by key, stamping `updated_by` with the caller.
    The path `key` is authoritative (the body key, if any, is ignored)."""
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if setting is None:
        setting = AppSetting(key=key)
        db.add(setting)

    setting.value = payload.value
    if payload.category is not None:
        setting.category = payload.category
    if payload.description is not None:
        setting.description = payload.description
    setting.updated_by = user.id

    db.commit()
    db.refresh(setting)
    return _serialize(setting)


@router.get("/settings/effective", response_model=dict, tags=["settings"])
def effective_settings(
    db: Session = Depends(get_db),
    _user: User = Depends(require_superadmin),
):
    """Effective platform configuration: sensible defaults overlaid with any
    persisted overrides. Read-only view of the current state. Secret values are
    masked. `source` flags whether each key comes from a default or an override."""
    rows = {s.key: s for s in db.query(AppSetting).all()}

    settings: dict = {}
    keys = set(DEFAULT_SETTINGS) | set(rows)
    for key in sorted(keys):
        default = DEFAULT_SETTINGS.get(key, {})
        row = rows.get(key)
        if row is not None:
            value = row.value if row.value not in (None, "") else default.get("value")
            category = row.category or default.get("category")
            description = row.description or default.get("description")
            source = "override"
        else:
            value = default.get("value")
            category = default.get("category")
            description = default.get("description")
            source = "default"
        settings[key] = {
            "key": key,
            "value": _mask_value(key, value),
            "category": category,
            "description": description,
            "source": source,
        }

    return {"settings": settings}
