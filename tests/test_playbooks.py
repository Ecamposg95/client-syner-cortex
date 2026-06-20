"""Endpoint tests for the internal Playbooks module.

Playbooks are CREW-ONLY: every route is gated by get_current_syner_crew, so a
CLIENT_USER must receive 403 on list/read/create/update/delete. Crew can do the
full CRUD. These tests run against an isolated in-memory SQLite DB so the dev
database is never touched (pattern from tests/test_policy_leak_endpoints.py).

Run:
    .venv/bin/python -m pytest tests/test_playbooks.py -q
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.security.auth import create_access_token

# Import model modules so all tables register on Base.metadata before create_all.
from app.models import models as m  # noqa: F401
from app.models import playbook as pb  # noqa: F401

from app.models.models import User, Organization, OrganizationUser

# The playbooks router is mounted on `app` by the orchestrator in production
# (BEFORE the SPA catch-all route). In this isolated suite we mount it ourselves
# (idempotently) so the test does not depend on main.py wiring. We insert the
# new routes at the FRONT of the route table so they win over the existing
# "/{catchall:path}" SPA fallback (which otherwise swallows GET /api/playbooks).
from app.routers import playbooks as playbooks_router

if not any(getattr(r, "path", "") == "/api/playbooks" for r in app.routes):
    _before = len(app.router.routes)
    app.include_router(playbooks_router.router, prefix="/api")
    _new = app.router.routes[_before:]
    del app.router.routes[_before:]
    app.router.routes[:0] = _new

ORG_SYNER = 1
ORG_A = 100

UID_CREW = 10
UID_CLIENT = 11


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
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed(s):
    s.add_all([
        Organization(id=ORG_SYNER, name="Syner", slug="syner", organization_type="SYNER"),
        Organization(id=ORG_A, name="Client A", slug="client-a", organization_type="CLIENT"),
    ])
    s.add_all([
        User(id=UID_CREW, email="crew@syner.io", hashed_password="x",
             full_name="Crew", user_type="SYNER_CREW", is_active=True),
        User(id=UID_CLIENT, email="client@a.io", hashed_password="x",
             full_name="Client", user_type="CLIENT_USER", is_active=True),
    ])
    s.add_all([
        OrganizationUser(organization_id=ORG_SYNER, user_id=UID_CREW, role="SYNER_PARTNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_CLIENT, role="CLIENT_OWNER"),
    ])
    s.commit()


def _headers(user_id: int, org_id: int = ORG_SYNER) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org_id)}


def crew_headers() -> dict:
    return _headers(UID_CREW, ORG_SYNER)


def client_headers() -> dict:
    return _headers(UID_CLIENT, ORG_A)


# --------------------------------------------------------------------------- #
# Crew: full CRUD
# --------------------------------------------------------------------------- #

def test_crew_create_list_get_update_delete(client):
    # Create
    r = client.post(
        "/api/playbooks",
        json={"title": "Diagnóstico 360", "category": "Diagnóstico",
              "content": "Pasos del método", "tags": ["interno", "core"]},
        headers=crew_headers(),
    )
    assert r.status_code == 200, r.text
    created = r.json()
    pid = created["id"]
    assert created["title"] == "Diagnóstico 360"
    assert created["category"] == "Diagnóstico"
    assert created["created_by"] == UID_CREW
    assert created["visibility"] == "INTERNAL_ONLY"
    assert created["tags"] == ["interno", "core"]

    # List
    r = client.get("/api/playbooks", headers=crew_headers())
    assert r.status_code == 200
    titles = {p["title"] for p in r.json()}
    assert "Diagnóstico 360" in titles

    # List filtered by category
    r = client.get("/api/playbooks", params={"category": "Diagnóstico"}, headers=crew_headers())
    assert r.status_code == 200
    assert all(p["category"] == "Diagnóstico" for p in r.json())

    r = client.get("/api/playbooks", params={"category": "NoExiste"}, headers=crew_headers())
    assert r.status_code == 200
    assert r.json() == []

    # Get one
    r = client.get(f"/api/playbooks/{pid}", headers=crew_headers())
    assert r.status_code == 200
    assert r.json()["id"] == pid

    # Update
    r = client.put(
        f"/api/playbooks/{pid}",
        json={"title": "Diagnóstico 360 v2", "content": "Pasos actualizados"},
        headers=crew_headers(),
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Diagnóstico 360 v2"
    assert r.json()["content"] == "Pasos actualizados"
    # untouched field preserved
    assert r.json()["category"] == "Diagnóstico"

    # Delete
    r = client.delete(f"/api/playbooks/{pid}", headers=crew_headers())
    assert r.status_code == 200
    assert r.json()["deleted_id"] == pid

    # Gone
    r = client.get(f"/api/playbooks/{pid}", headers=crew_headers())
    assert r.status_code == 404


def test_crew_get_missing_404(client):
    r = client.get("/api/playbooks/999999", headers=crew_headers())
    assert r.status_code == 404


# --------------------------------------------------------------------------- #
# Client: 403 on every endpoint (crew-only gate)
# --------------------------------------------------------------------------- #

def test_client_list_forbidden(client):
    r = client.get("/api/playbooks", headers=client_headers())
    assert r.status_code == 403


def test_client_get_forbidden(client):
    r = client.get("/api/playbooks/1", headers=client_headers())
    assert r.status_code == 403


def test_client_create_forbidden(client):
    r = client.post("/api/playbooks", json={"title": "x"}, headers=client_headers())
    assert r.status_code == 403


def test_client_update_forbidden(client):
    r = client.put("/api/playbooks/1", json={"title": "x"}, headers=client_headers())
    assert r.status_code == 403


def test_client_delete_forbidden(client):
    r = client.delete("/api/playbooks/1", headers=client_headers())
    assert r.status_code == 403
