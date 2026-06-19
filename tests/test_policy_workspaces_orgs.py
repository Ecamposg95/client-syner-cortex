"""Policy-gate tests for the management capabilities of the workspaces and
organizations routers (Task Pack §8, Fase 3 PR2 wiring).

These encode the §8 matrix on the two routers whose guards were previously
LAXER than the matrix:

  - POST /workspaces (CREATE_WORKSPACE) — ALLOW only for crew
    (SYNER_ADMIN / SYNER_PARTNER / SYNER_CONSULTANT). A CLIENT_* user must NOT
    be able to create a workspace anymore.
  - POST /organizations (CREATE_CLIENT) — ALLOW only for SYNER_ADMIN
    (SUPERADMIN allow-all). A crew acting as the default SYNER_PARTNER, and any
    CLIENT_* user, must be rejected.
  - POST /organizations/users (CONFIGURE_MODULES) — ALLOW only SYNER_ADMIN /
    superadmin; a CLIENT_OWNER can no longer self-manage members.

It also pins the behaviour that must be PRESERVED:
  - GET /organizations keeps its special crew cross-client logic (a crew user
    sees every org, not only its membership rows).

Same harness as tests/test_policy_leak_endpoints.py: real endpoints through
FastAPI's TestClient over an isolated in-memory SQLite DB.

Run:
    .venv/bin/python -m pytest tests/test_policy_workspaces_orgs.py -q
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.security.auth import create_access_token

# Register every model module so all tables exist before create_all.
from app.models import models as m  # noqa: F401
from app.models import clevel as cl  # noqa: F401
from app.models import insight as ins  # noqa: F401
from app.models import raci as rc  # noqa: F401
from app.models import kpi as kp  # noqa: F401
from app.models import toolkit as tk  # noqa: F401

from app.models.models import User, Organization, OrganizationUser, Workspace


# --------------------------------------------------------------------------- #
# Isolated DB + dependency override
# --------------------------------------------------------------------------- #

ORG_SYNER = 1    # the Syner internal firm org
ORG_A = 100      # client org A

UID_ADMIN = 10   # crew with SYNER_ADMIN membership in ORG_SYNER
UID_PARTNER = 11  # crew with SYNER_PARTNER membership in ORG_SYNER
UID_SUPER = 12   # platform superadmin
UID_A_OWNER = 13  # client CLIENT_OWNER in ORG_A
UID_A_VIEWER = 14  # client CLIENT_VIEWER in ORG_A, never mutated by any test


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    _seed(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    # kpi router binds its own get_db; override it too so nothing hits the dev DB.
    from app.routers import kpi as kpi_router
    app.dependency_overrides[kpi_router.get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed(s):
    # --- Organizations ---
    s.add_all([
        Organization(id=ORG_SYNER, name="Syner", slug="syner", organization_type="SYNER"),
        Organization(id=ORG_A, name="Client A", slug="client-a", organization_type="CLIENT"),
    ])

    # --- Users ---
    s.add_all([
        User(id=UID_ADMIN, email="admin@syner.io", hashed_password="x",
             full_name="Admin", user_type="SYNER_CREW", is_active=True),
        User(id=UID_PARTNER, email="partner@syner.io", hashed_password="x",
             full_name="Partner", user_type="SYNER_CREW", is_active=True),
        User(id=UID_SUPER, email="super@syner.io", hashed_password="x",
             full_name="Super", user_type="SYNER_CREW", is_active=True,
             is_superadmin=True),
        User(id=UID_A_OWNER, email="ownerA@a.io", hashed_password="x",
             full_name="Owner A", user_type="CLIENT_USER", is_active=True),
        User(id=UID_A_VIEWER, email="viewerA@a.io", hashed_password="x",
             full_name="Viewer A", user_type="CLIENT_USER", is_active=True),
    ])

    # --- Memberships ---
    # Crew carry their real role in the Syner firm org; they act cross-client as
    # SYNER_PARTNER on a client org without an explicit membership row.
    s.add_all([
        OrganizationUser(organization_id=ORG_SYNER, user_id=UID_ADMIN, role="SYNER_ADMIN"),
        OrganizationUser(organization_id=ORG_SYNER, user_id=UID_PARTNER, role="SYNER_PARTNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_OWNER, role="CLIENT_OWNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_VIEWER, role="CLIENT_VIEWER"),
    ])

    # A workspace already in org A (so the client has org context).
    s.add(Workspace(id=1000, organization_id=ORG_A, name="WS A"))

    s.commit()


# --------------------------------------------------------------------------- #
# Auth helpers
# --------------------------------------------------------------------------- #

def _headers(user_id: int, org_id: int) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org_id)}


def admin_headers(org_id: int = ORG_SYNER) -> dict:
    return _headers(UID_ADMIN, org_id)


def partner_headers(org_id: int = ORG_A) -> dict:
    return _headers(UID_PARTNER, org_id)


def super_headers(org_id: int = ORG_A) -> dict:
    return _headers(UID_SUPER, org_id)


def clientA_headers(org_id: int = ORG_A) -> dict:
    return _headers(UID_A_OWNER, org_id)


# =========================================================================== #
# POST /api/workspaces  — CREATE_WORKSPACE (crew only)
# =========================================================================== #

def test_create_workspace_client_forbidden(client):
    """A CLIENT_OWNER may NOT create a workspace (§8: crew-only). Previously the
    guard allowed CLIENT_OWNER/CLIENT_EXECUTIVE — now it must 403."""
    r = client.post("/api/workspaces", json={"name": "client-made"},
                    headers=clientA_headers())
    assert r.status_code == 403


def test_create_workspace_crew_partner_allowed(client):
    """Crew acting as SYNER_PARTNER on the client org may create a workspace."""
    r = client.post("/api/workspaces", json={"name": "ws-by-partner"},
                    headers=partner_headers(ORG_A))
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "ws-by-partner"
    assert body["organization_id"] == ORG_A


def test_create_workspace_admin_allowed(client):
    """SYNER_ADMIN (in the Syner org) may create a workspace there."""
    r = client.post("/api/workspaces", json={"name": "ws-by-admin"},
                    headers=admin_headers(ORG_SYNER))
    assert r.status_code == 201
    assert r.json()["organization_id"] == ORG_SYNER


def test_create_workspace_superadmin_allowed(client):
    """Superadmin bypasses every role constraint (allow-all)."""
    r = client.post("/api/workspaces", json={"name": "ws-by-super"},
                    headers=super_headers(ORG_A))
    assert r.status_code == 201


def test_list_workspaces_client_still_allowed(client):
    """PRESERVED: listing stays org-scoped — a validated client member can still
    enumerate its own org's workspaces (reading needs no management capability)."""
    r = client.get("/api/workspaces", headers=clientA_headers())
    assert r.status_code == 200
    org_ids = {w["organization_id"] for w in r.json()}
    assert org_ids <= {ORG_A}  # never another org's workspaces


# =========================================================================== #
# POST /api/organizations  — CREATE_CLIENT (SYNER_ADMIN / superadmin only)
# =========================================================================== #

def test_create_client_org_client_forbidden(client):
    """A CLIENT_USER may NOT create a client organization (§8: SYNER_ADMIN only).
    Closes the old self-signup path where any authenticated user could."""
    r = client.post("/api/organizations", json={"name": "New Client Co"},
                    headers=clientA_headers())
    assert r.status_code == 403


def test_create_client_org_partner_forbidden(client):
    """Crew acting as the default SYNER_PARTNER is NOT SYNER_ADMIN → denied."""
    r = client.post("/api/organizations", json={"name": "Partner Co"},
                    headers=partner_headers(ORG_A))
    assert r.status_code == 403


def test_create_client_org_admin_allowed(client):
    """SYNER_ADMIN (resolved via Syner-org membership) may create a client."""
    r = client.post("/api/organizations", json={"name": "Admin Client Co"},
                    headers=admin_headers(ORG_SYNER))
    assert r.status_code == 201
    assert r.json()["name"] == "Admin Client Co"


def test_create_client_org_superadmin_allowed(client):
    """Superadmin allow-all."""
    r = client.post("/api/organizations", json={"name": "Super Client Co"},
                    headers=super_headers(ORG_A))
    assert r.status_code == 201


# =========================================================================== #
# POST /api/organizations/users  — CONFIGURE_MODULES (SYNER_ADMIN / superadmin)
# =========================================================================== #

def test_add_user_client_owner_forbidden(client):
    """A CLIENT_OWNER may no longer add members on its own (§8: CONFIGURE_MODULES
    is SYNER_ADMIN-only)."""
    r = client.post("/api/organizations/users",
                    json={"email": "admin@syner.io", "role": "CLIENT_MANAGER"},
                    headers=clientA_headers())
    assert r.status_code == 403


def test_add_user_admin_allowed(client):
    """SYNER_ADMIN may add an existing user to the org it administers."""
    r = client.post("/api/organizations/users",
                    json={"email": "ownerA@a.io", "role": "CLIENT_MANAGER"},
                    headers=admin_headers(ORG_SYNER))
    # ownerA isn't a member of ORG_SYNER yet, so this should succeed (201).
    assert r.status_code == 201


# =========================================================================== #
# GET /api/organizations  — PRESERVED crew cross-client logic (do NOT break it)
# =========================================================================== #

def test_get_organizations_crew_sees_every_org(client):
    """PRESERVED: crew (and superadmin) see EVERY org, not just membership rows."""
    r = client.get("/api/organizations", headers=partner_headers(ORG_A))
    assert r.status_code == 200
    org_ids = {row["organization_id"] for row in r.json()}
    assert {ORG_SYNER, ORG_A} <= org_ids


def test_get_organizations_client_sees_only_membership(client):
    """PRESERVED: a client sees only the orgs it is actually a member of (not the
    whole portfolio the way crew does). Uses a client whose memberships no test
    mutates, so the assertion is exact."""
    r = client.get("/api/organizations", headers=_headers(UID_A_VIEWER, ORG_A))
    assert r.status_code == 200
    org_ids = {row["organization_id"] for row in r.json()}
    assert org_ids == {ORG_A}
