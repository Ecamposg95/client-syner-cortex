"""Crew-only firm governance endpoints: /admin/users and /admin/modules.

Verifies (Task Pack "Gestión de la firma"):
  * Crew can list ALL users of the firm cross-org, with their orgs/roles.
  * Crew can list the Module catalog and create a new module.
  * A CLIENT_USER receives 403 on every one of these endpoints.

Runs against an isolated in-memory SQLite DB so the dev database is never
touched (same pattern as test_policy_leak_endpoints.py).

Run:
    .venv/bin/python -m pytest tests/test_admin_firm.py -q
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.security.auth import create_access_token

# Register every model on Base.metadata before create_all.
from app.models import models as m  # noqa: F401
from app.models import clevel as cl  # noqa: F401
from app.models import insight as ins  # noqa: F401
from app.models import raci as rc  # noqa: F401
from app.models import kpi as kp  # noqa: F401
from app.models import toolkit as tk  # noqa: F401

from app.models.models import (
    User, Organization, OrganizationUser, Module,
)


# Org ids
ORG_SYNER = 1
ORG_A = 100
ORG_B = 200

# User ids
UID_CREW = 10
UID_A_OWNER = 11
UID_B_OWNER = 12


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
    from app.routers import kpi as kpi_router
    app.dependency_overrides[kpi_router.get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed(s):
    s.add_all([
        Organization(id=ORG_SYNER, name="Syner", slug="syner", organization_type="SYNER"),
        Organization(id=ORG_A, name="Client A", slug="client-a", organization_type="CLIENT"),
        Organization(id=ORG_B, name="Client B", slug="client-b", organization_type="CLIENT"),
    ])
    s.add_all([
        User(id=UID_CREW, email="crew@syner.io", hashed_password="x",
             full_name="Crew", user_type="SYNER_CREW", is_active=True),
        User(id=UID_A_OWNER, email="ownerA@a.io", hashed_password="x",
             full_name="Owner A", user_type="CLIENT_USER", is_active=True),
        User(id=UID_B_OWNER, email="ownerB@b.io", hashed_password="x",
             full_name="Owner B", user_type="CLIENT_USER", is_active=True),
    ])
    s.add_all([
        OrganizationUser(organization_id=ORG_SYNER, user_id=UID_CREW, role="SYNER_PARTNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_OWNER, role="CLIENT_OWNER"),
        OrganizationUser(organization_id=ORG_B, user_id=UID_B_OWNER, role="CLIENT_OWNER"),
    ])
    s.add(Module(id=1, code="cortex_vault", name="Cortex Vault", description="Doc vault"))
    s.commit()


def _headers(user_id: int, org_id: int) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org_id)}


def crew_headers(org_id: int = ORG_SYNER) -> dict:
    return _headers(UID_CREW, org_id)


def client_headers(org_id: int = ORG_A) -> dict:
    return _headers(UID_A_OWNER, org_id)


# =========================================================================== #
# /admin/users
# =========================================================================== #

def test_crew_lists_all_users_cross_org(client):
    r = client.get("/api/admin/users", headers=crew_headers())
    assert r.status_code == 200
    body = r.json()
    by_email = {u["email"]: u for u in body}
    # All three firm users are present, regardless of org.
    assert {"crew@syner.io", "ownerA@a.io", "ownerB@b.io"} <= set(by_email)

    # Owner A carries org membership with the right role.
    owner_a = by_email["ownerA@a.io"]
    assert owner_a["user_type"] == "CLIENT_USER"
    assert owner_a["is_active"] is True
    org_names = {o["org_name"] for o in owner_a["orgs"]}
    roles = {o["role"] for o in owner_a["orgs"]}
    assert "Client A" in org_names
    assert "CLIENT_OWNER" in roles

    # Crew belongs to the Syner org.
    crew = by_email["crew@syner.io"]
    assert {o["org_name"] for o in crew["orgs"]} == {"Syner"}


def test_client_forbidden_on_users(client):
    r = client.get("/api/admin/users", headers=client_headers())
    assert r.status_code == 403


# =========================================================================== #
# /admin/modules
# =========================================================================== #

def test_crew_lists_modules(client):
    r = client.get("/api/admin/modules", headers=crew_headers())
    assert r.status_code == 200
    codes = {m["code"] for m in r.json()}
    assert "cortex_vault" in codes


def test_crew_creates_module(client):
    payload = {"code": "cortex_chat", "name": "Cortex Chat", "description": "Chat module"}
    r = client.post("/api/admin/modules", json=payload, headers=crew_headers())
    assert r.status_code == 201
    created = r.json()
    assert created["code"] == "cortex_chat"
    assert created["id"] > 0

    # It now appears in the catalog listing.
    r2 = client.get("/api/admin/modules", headers=crew_headers())
    assert "cortex_chat" in {m["code"] for m in r2.json()}


def test_create_duplicate_module_rejected(client):
    payload = {"code": "cortex_vault", "name": "Dup", "description": None}
    r = client.post("/api/admin/modules", json=payload, headers=crew_headers())
    assert r.status_code == 400


def test_client_forbidden_on_modules_list(client):
    r = client.get("/api/admin/modules", headers=client_headers())
    assert r.status_code == 403


def test_client_forbidden_on_module_create(client):
    payload = {"code": "evil_mod", "name": "Evil", "description": None}
    r = client.post("/api/admin/modules", json=payload, headers=client_headers())
    assert r.status_code == 403
    # And nothing was created.
    r2 = client.get("/api/admin/modules", headers=crew_headers())
    assert "evil_mod" not in {m["code"] for m in r2.json()}
