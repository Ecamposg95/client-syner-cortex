"""Provision the platform's reference modules and the initial Syner crew admin.

Credentials come from the environment (never hardcoded):
    SYNER_ADMIN_EMAIL, SYNER_ADMIN_PASSWORD

Run explicitly (idempotent):
    python -m app.scripts.bootstrap_admin

Re-running rotates the admin password to the current env value and ensures the
admin is SYNER_CREW / superadmin, linked to the Syner organization.
"""
import os
import sys

from app.database import SessionLocal
import app.models.models  # noqa: F401  (ensure models are registered)
from app.models.models import Module, User, Organization, OrganizationUser
from app.security.auth import get_password_hash

MODULES = [
    ("Cortex Vault", "cortex_vault", "RAG enterprise knowledge vault"),
    ("Cortex Chat", "cortex_chat", "Context-aware AI consultant chat"),
    ("Cortex Diagnose", "cortex_diagnose", "360-degree business diagnostics"),
    ("Cortex Agents", "cortex_agents", "Specialized AI consulting agents"),
    ("Cortex Insights", "cortex_insights", "Business metrics analysis & alarms"),
    ("Cortex Reports", "cortex_reports", "Boardroom executive briefings compiler"),
    ("Cortex Roadmap", "cortex_roadmap", "30/60/90 execution roadmap backlog"),
    ("Cortex Boardroom", "cortex_boardroom", "C-Suite executive boardroom KPI dashboard"),
]


def bootstrap():
    email = os.getenv("SYNER_ADMIN_EMAIL")
    password = os.getenv("SYNER_ADMIN_PASSWORD")
    if not email or not password:
        sys.exit(
            "ERROR: set SYNER_ADMIN_EMAIL and SYNER_ADMIN_PASSWORD in the environment "
            "(or .env) before running bootstrap_admin."
        )

    db = SessionLocal()
    try:
        # 1. Reference modules (idempotent by code)
        existing_codes = {m.code for m in db.query(Module).all()}
        for name, code, desc in MODULES:
            if code not in existing_codes:
                db.add(Module(name=name, code=code, description=desc))
        db.flush()

        # 2. Syner organization (idempotent by slug)
        org = db.query(Organization).filter(Organization.slug == "syner-consulting").first()
        if not org:
            org = Organization(name="Syner Consulting Org", slug="syner-consulting",
                               organization_type="SYNER")
            db.add(org)
            db.flush()

        # 3. Admin user — create or rotate password
        admin = db.query(User).filter(User.email == email).first()
        if admin:
            admin.hashed_password = get_password_hash(password)
            admin.user_type = "SYNER_CREW"
            admin.is_superadmin = True
            admin.is_active = True
            admin.must_change_password = False
            action = "updated (password rotated)"
        else:
            admin = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name="Syner Admin",
                user_type="SYNER_CREW",
                is_active=True,
                is_superadmin=True,
                must_change_password=False,
            )
            db.add(admin)
            db.flush()
            action = "created"

        # 4. Link admin to Syner org as SUPERADMIN (idempotent)
        link = db.query(OrganizationUser).filter(
            OrganizationUser.organization_id == org.id,
            OrganizationUser.user_id == admin.id,
        ).first()
        if not link:
            db.add(OrganizationUser(organization_id=org.id, user_id=admin.id, role="SUPERADMIN"))

        db.commit()
        print(f"✅ Bootstrap complete. Modules ensured. Admin {email} {action}.")
    except Exception as e:
        db.rollback()
        print(f"❌ Bootstrap failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap()
