"""Crew administration console: onboard client companies, users, modules and
workspaces. Every endpoint is gated to the internal Syner Crew."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import secrets
import datetime

from app.database import get_db
from app.dependencies import get_current_syner_crew
from app.models.models import (
    Organization, OrganizationUser, User, Module, OrganizationModule, Workspace
)
from app.security.auth import get_password_hash
from app.policy import roles
from app.policy.validation import validate_org_role

router = APIRouter(prefix="/admin", tags=["admin"])

# Canonical client roles (Task Pack §5). Sourced from app.policy.roles so the
# set can't drift (it previously omitted CLIENT_CONTRIBUTOR).
CLIENT_ROLES = set(roles.CLIENT_ROLES)


# ─────────────────────────── Schemas ───────────────────────────
class ClientCreate(BaseModel):
    name: str
    owner_email: Optional[EmailStr] = None
    owner_full_name: Optional[str] = None
    owner_password: Optional[str] = None       # temp password; generated if omitted


class ClientUserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "CLIENT_VIEWER"
    password: Optional[str] = None             # temp password; generated if omitted


class ModuleToggle(BaseModel):
    code: str
    enabled: bool


class ModulesUpdate(BaseModel):
    modules: List[ModuleToggle]


class WorkspaceCreateIn(BaseModel):
    name: str
    description: Optional[str] = None


# ─────────────────────────── Helpers ───────────────────────────
def _gen_temp_password() -> str:
    return secrets.token_urlsafe(9)


def _unique_slug(db: Session, name: str) -> str:
    base = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-") or "client"
    slug = base
    i = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        i += 1
        slug = f"{base}-{i}"
    return slug


def _create_client_user(db: Session, org_id: int, email: str, full_name: Optional[str],
                        role: str, password: Optional[str]) -> dict:
    # Must be a canonical role (Task Pack §5) — and specifically a client role.
    try:
        validate_org_role(role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if role not in CLIENT_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of {sorted(CLIENT_ROLES)}")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="A user with this email already exists.")
    temp = password or _gen_temp_password()
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(temp),
        user_type="CLIENT_USER",
        is_active=True,
        is_superadmin=False,
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    db.add(OrganizationUser(organization_id=org_id, user_id=user.id, role=role))
    return {"user_id": user.id, "email": email, "role": role, "temp_password": temp}


# ─────────────────────────── Endpoints ───────────────────────────
@router.get("/clients")
def list_clients(db: Session = Depends(get_db), _crew: User = Depends(get_current_syner_crew)):
    orgs = db.query(Organization).filter(Organization.organization_type == "CLIENT").all()
    out = []
    for o in orgs:
        users = db.query(OrganizationUser).filter(OrganizationUser.organization_id == o.id).count()
        workspaces = db.query(Workspace).filter(Workspace.organization_id == o.id).count()
        modules = db.query(OrganizationModule).filter(
            OrganizationModule.organization_id == o.id, OrganizationModule.is_enabled == True
        ).count()
        out.append({
            "id": o.id, "name": o.name, "slug": o.slug,
            "organization_type": o.organization_type, "created_at": o.created_at,
            "user_count": users, "workspace_count": workspaces, "enabled_module_count": modules,
        })
    return out


@router.post("/clients", status_code=status.HTTP_201_CREATED)
def create_client(data: ClientCreate, db: Session = Depends(get_db),
                  _crew: User = Depends(get_current_syner_crew)):
    org = Organization(
        name=data.name, slug=_unique_slug(db, data.name), organization_type="CLIENT"
    )
    db.add(org)
    db.flush()

    owner = None
    if data.owner_email:
        owner = _create_client_user(
            db, org.id, data.owner_email, data.owner_full_name, "CLIENT_OWNER", data.owner_password
        )

    db.commit()
    db.refresh(org)
    return {
        "id": org.id, "name": org.name, "slug": org.slug,
        "organization_type": org.organization_type, "created_at": org.created_at,
        "owner": owner,   # includes temp_password to share with the client
    }


@router.get("/clients/{org_id}")
def get_client(org_id: int, db: Session = Depends(get_db),
               _crew: User = Depends(get_current_syner_crew)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Client organization not found")

    users = db.query(OrganizationUser, User).join(User, OrganizationUser.user_id == User.id).filter(
        OrganizationUser.organization_id == org_id
    ).all()
    workspaces = db.query(Workspace).filter(Workspace.organization_id == org_id).all()

    enabled = {
        om.module_id: om.is_enabled
        for om in db.query(OrganizationModule).filter(OrganizationModule.organization_id == org_id).all()
    }
    modules = [
        {"code": m.code, "name": m.name, "description": m.description,
         "enabled": bool(enabled.get(m.id, False))}
        for m in db.query(Module).all()
    ]

    return {
        "id": org.id, "name": org.name, "slug": org.slug,
        "organization_type": org.organization_type, "created_at": org.created_at,
        "users": [
            {"user_id": u.id, "email": u.email, "full_name": u.full_name,
             "role": ou.role, "must_change_password": u.must_change_password,
             "is_active": u.is_active}
            for ou, u in users
        ],
        "workspaces": [{"id": w.id, "name": w.name, "description": w.description} for w in workspaces],
        "modules": modules,
    }


@router.post("/clients/{org_id}/users", status_code=status.HTTP_201_CREATED)
def create_client_user(org_id: int, data: ClientUserCreate, db: Session = Depends(get_db),
                       _crew: User = Depends(get_current_syner_crew)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Client organization not found")
    result = _create_client_user(db, org_id, data.email, data.full_name, data.role, data.password)
    db.commit()
    return result


@router.put("/clients/{org_id}/modules")
def update_client_modules(org_id: int, data: ModulesUpdate, db: Session = Depends(get_db),
                          _crew: User = Depends(get_current_syner_crew)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Client organization not found")

    for toggle in data.modules:
        module = db.query(Module).filter(Module.code == toggle.code).first()
        if not module:
            raise HTTPException(status_code=404, detail=f"Module '{toggle.code}' not found")
        link = db.query(OrganizationModule).filter(
            OrganizationModule.organization_id == org_id,
            OrganizationModule.module_id == module.id
        ).first()
        if link:
            link.is_enabled = toggle.enabled
        else:
            db.add(OrganizationModule(
                organization_id=org_id, module_id=module.id, is_enabled=toggle.enabled
            ))
    db.commit()
    return {"message": "Modules updated", "count": len(data.modules)}


@router.post("/clients/{org_id}/workspaces", status_code=status.HTTP_201_CREATED)
def create_client_workspace(org_id: int, data: WorkspaceCreateIn, db: Session = Depends(get_db),
                            _crew: User = Depends(get_current_syner_crew)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Client organization not found")
    ws = Workspace(organization_id=org_id, name=data.name, description=data.description)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return {"id": ws.id, "name": ws.name, "description": ws.description,
            "organization_id": ws.organization_id, "created_at": ws.created_at}
