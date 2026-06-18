"""Provision BJX Motors as a real client organization (idempotent).

Creates / ensures:
  - Organization "BJX Motors" (slug bjx-motors, type CLIENT)
  - Owner user jorge@bjxmotors.com (CLIENT_OWNER, must change password)
  - All platform modules enabled for the org
  - The 4 working workspaces (Gobernanza, Operaciones, Cultura, EHS)
  - C-Level consulting data (engagement, findings, risks, decisions) via
    seed_clevel_bjx, so the portal / Insights show real content.

Initial owner password comes from BJX_OWNER_PASSWORD; if unset, a random one is
generated and printed. Re-running never clobbers an existing user/org.

Run explicitly:
    python -m app.scripts.seed_bjx_client
"""
import os
import secrets

from app.database import SessionLocal
import app.models.models  # noqa: F401
from app.models.models import (
    Organization, OrganizationUser, User, Module, OrganizationModule, Workspace,
)
from app.models.clevel import ConsultingEngagement
from app.security.auth import get_password_hash

OWNER_EMAIL = "jorge@bjxmotors.com"
OWNER_NAME = "Jorge (BJX Motors)"
WORKSPACES = [
    ("Gobernanza y Estrategia", "Gobierno corporativo, comités y estrategia."),
    ("Operaciones y Estandarización", "Macroflujos, SOPs y franchise-ready pack."),
    ("Cultura y Capacitación", "Academia Pit Crew y adopción."),
    ("Seguridad y EHS", "Higiene, seguridad y manejo de residuos."),
]


def seed_bjx_client():
    owner_password = os.getenv("BJX_OWNER_PASSWORD")
    generated = False
    if not owner_password:
        owner_password = secrets.token_urlsafe(9)
        generated = True

    db = SessionLocal()
    try:
        # 1. Organization (idempotent by slug)
        org = db.query(Organization).filter(Organization.slug == "bjx-motors").first()
        if not org:
            org = Organization(name="BJX Motors", slug="bjx-motors", organization_type="CLIENT")
            db.add(org)
            db.flush()
            org_action = "created"
        else:
            org_action = "already existed"

        # 2. Owner user (idempotent by email; never clobber)
        owner = db.query(User).filter(User.email == OWNER_EMAIL).first()
        owner_created = False
        if not owner:
            owner = User(
                email=OWNER_EMAIL,
                full_name=OWNER_NAME,
                hashed_password=get_password_hash(owner_password),
                user_type="CLIENT_USER",
                is_active=True,
                is_superadmin=False,
                must_change_password=True,
            )
            db.add(owner)
            db.flush()
            owner_created = True
        # Link owner to org (idempotent)
        link = db.query(OrganizationUser).filter(
            OrganizationUser.organization_id == org.id,
            OrganizationUser.user_id == owner.id,
        ).first()
        if not link:
            db.add(OrganizationUser(organization_id=org.id, user_id=owner.id, role="CLIENT_OWNER"))

        # 3. Enable all modules for the org (idempotent)
        existing_mod = {
            om.module_id
            for om in db.query(OrganizationModule).filter(OrganizationModule.organization_id == org.id).all()
        }
        modules = db.query(Module).all()
        for m in modules:
            if m.id not in existing_mod:
                db.add(OrganizationModule(organization_id=org.id, module_id=m.id, is_enabled=True))

        # 4. Workspaces (idempotent by name)
        existing_ws = {
            w.name for w in db.query(Workspace).filter(Workspace.organization_id == org.id).all()
        }
        for name, desc in WORKSPACES:
            if name not in existing_ws:
                db.add(Workspace(organization_id=org.id, name=name, description=desc))

        # First-run only: don't re-seed (and overwrite) consulting data on every deploy.
        needs_clevel = db.query(ConsultingEngagement).filter(
            ConsultingEngagement.organization_id == org.id).first() is None

        db.commit()
        print(f"✅ BJX client: org {org_action} (id={org.id}). "
              f"Owner {OWNER_EMAIL} {'created' if owner_created else 'already existed'}. "
              f"Modules enabled: {len(modules)}. Workspaces ensured: {len(WORKSPACES)}.")
        if owner_created:
            if generated:
                print(f"🔑 Temporary owner password: {owner_password} (set BJX_OWNER_PASSWORD to choose your own).")
            else:
                print("🔑 Temporary owner password: value of BJX_OWNER_PASSWORD (must change on first login).")
    except Exception as e:
        db.rollback()
        print(f"❌ BJX client seed failed: {e}")
        raise
    finally:
        db.close()

    # 5. C-Level consulting data (engagement, findings, risks, decisions) — only
    #    the first time, so client-side changes aren't wiped on later deploys.
    if needs_clevel:
        try:
            from app.seed.seed_clevel_bjx import seed_clevel_bjx
            seed_clevel_bjx()
        except Exception as e:
            print(f"⚠️  C-Level data seed skipped: {e}")
    else:
        print("ℹ️  C-Level data already present; skipping (preserves client changes).")


if __name__ == "__main__":
    seed_bjx_client()
