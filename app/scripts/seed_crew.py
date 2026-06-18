"""Provision the initial Syner crew users (idempotent).

Creates the platform reference modules, the Syner organization, and these crew
accounts the first time it runs:

    ecg@syner.mx        -> superadmin   (SYNER_CREW, is_superadmin, org SUPERADMIN)
    humberto@syner.mx   -> admin        (SYNER_CREW, org SYNER_PARTNER)
    alan@syner.mx       -> admin        (SYNER_CREW, org SYNER_PARTNER)
    damian@syner.mx     -> admin        (SYNER_CREW, org SYNER_PARTNER)

Initial password comes from CREW_SEED_PASSWORD; if unset, a random temporary one
is generated and printed. Every account is forced to change its password on first
login (must_change_password=True). Existing accounts are left untouched (no
password clobber), so re-running on each deploy is safe.

Run explicitly:
    python -m app.scripts.seed_crew
"""
import os
import secrets
import sys

from app.database import SessionLocal
import app.models.models  # noqa: F401  (ensure models are registered)
from app.models.models import Module, User, Organization, OrganizationUser
from app.security.auth import get_password_hash
from app.scripts.bootstrap_admin import MODULES

# (email, full_name, is_superadmin, org_role)
CREW = [
    ("ecg@syner.mx",      "ECG (Superadmin)", True,  "SUPERADMIN"),
    ("humberto@syner.mx", "Humberto",         False, "SYNER_PARTNER"),
    ("alan@syner.mx",     "Alan",             False, "SYNER_PARTNER"),
    ("damian@syner.mx",   "Damian",           False, "SYNER_PARTNER"),
]


def seed():
    # Shared temporary password (rotated on first login). Prefer an explicit env
    # value so the operator knows it; otherwise generate and surface one.
    temp_password = os.getenv("CREW_SEED_PASSWORD")
    generated = False
    if not temp_password:
        temp_password = secrets.token_urlsafe(12)
        generated = True

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

        # 3. Crew users — create if missing (never clobber an existing password)
        created, skipped = [], []
        for email, full_name, is_super, org_role in CREW:
            user = db.query(User).filter(User.email == email).first()
            if user:
                skipped.append(email)
            else:
                user = User(
                    email=email,
                    hashed_password=get_password_hash(temp_password),
                    full_name=full_name,
                    user_type="SYNER_CREW",
                    is_active=True,
                    is_superadmin=is_super,
                    must_change_password=True,
                )
                db.add(user)
                db.flush()
                created.append(email)

            # 4. Link to Syner org with the right role (idempotent)
            link = db.query(OrganizationUser).filter(
                OrganizationUser.organization_id == org.id,
                OrganizationUser.user_id == user.id,
            ).first()
            if not link:
                db.add(OrganizationUser(organization_id=org.id, user_id=user.id, role=org_role))

        db.commit()

        print(f"✅ Seed crew complete. Created: {created or 'none'}. "
              f"Already existed (unchanged): {skipped or 'none'}.")
        if created:
            if generated:
                print(f"🔑 Temporary password for the new accounts: {temp_password}")
                print("   (set CREW_SEED_PASSWORD to choose your own; users must change it on first login)")
            else:
                print("🔑 Temporary password: value of CREW_SEED_PASSWORD "
                      "(users must change it on first login).")
    except Exception as e:
        db.rollback()
        print(f"❌ Seed crew failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
