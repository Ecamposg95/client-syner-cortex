"""Endpoint-level policy tests for /roadmaps/* and /diagnoses/* (Fase 3, PR2).

INVARIANT (Task Pack §4): a CLIENT_USER must NEVER see, through these endpoints,
(a) data of ANOTHER organization, nor (b) roadmaps/diagnoses of its OWN org in an
internal state (INTERNAL_ONLY, DRAFT_INTERNAL, APPROVED-but-not-shared, ...).
Syner crew (SYNER_CREW) see everything within their scope.

Mirrors the harness of tests/test_policy_leak_endpoints.py: an isolated in-memory
SQLite DB (StaticPool, single connection), get_db overridden, JWT tokens via
create_access_token, and the X-Organization-ID header carrying the active org.

Run:
    .venv/bin/python -m pytest tests/test_policy_roadmaps_diagnoses.py -q
"""
import datetime as _dt

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
    User, Organization, OrganizationUser, Workspace,
    Diagnosis, Roadmap, RoadmapItem,
)


# --------------------------------------------------------------------------- #
# Ids
# --------------------------------------------------------------------------- #
ORG_A = 100   # client org A
ORG_B = 200   # client org B
ORG_SYNER = 1  # Syner internal org

UID_CREW = 10
UID_A_OWNER = 11
UID_B_OWNER = 12

WS_A = 1000
WS_B = 2000


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
    # --- Organizations ---
    s.add_all([
        Organization(id=ORG_SYNER, name="Syner", slug="syner", organization_type="SYNER"),
        Organization(id=ORG_A, name="Client A", slug="client-a", organization_type="CLIENT"),
        Organization(id=ORG_B, name="Client B", slug="client-b", organization_type="CLIENT"),
    ])

    # --- Users ---
    s.add_all([
        User(id=UID_CREW, email="crew@syner.io", hashed_password="x",
             full_name="Crew", user_type="SYNER_CREW", is_active=True),
        User(id=UID_A_OWNER, email="ownerA@a.io", hashed_password="x",
             full_name="Owner A", user_type="CLIENT_USER", is_active=True),
        User(id=UID_B_OWNER, email="ownerB@b.io", hashed_password="x",
             full_name="Owner B", user_type="CLIENT_USER", is_active=True),
    ])

    # --- Memberships ---
    s.add_all([
        OrganizationUser(organization_id=ORG_SYNER, user_id=UID_CREW, role="SYNER_PARTNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_OWNER, role="CLIENT_OWNER"),
        OrganizationUser(organization_id=ORG_B, user_id=UID_B_OWNER, role="CLIENT_OWNER"),
    ])

    # --- Workspaces ---
    s.add(Workspace(id=WS_A, organization_id=ORG_A, name="WS A"))
    s.add(Workspace(id=WS_B, organization_id=ORG_B, name="WS B"))

    # --- Diagnoses in org A: client-visible (id=1) + internal (id=2, newest) ---
    s.add(Diagnosis(id=1, workspace_id=WS_A, organization_id=ORG_A, user_id=UID_CREW,
                    status="COMPLETED", visibility="CLIENT_VISIBLE",
                    created_at=_dt.datetime(2024, 1, 1)))
    s.add(Diagnosis(id=2, workspace_id=WS_A, organization_id=ORG_A, user_id=UID_CREW,
                    status="COMPLETED", visibility="INTERNAL_ONLY",
                    created_at=_dt.datetime(2024, 6, 1)))
    # A diagnosis in org B (cross-org probing).
    s.add(Diagnosis(id=3, workspace_id=WS_B, organization_id=ORG_B, user_id=UID_CREW,
                    status="COMPLETED", visibility="CLIENT_VISIBLE",
                    created_at=_dt.datetime(2024, 1, 1)))

    # --- Roadmaps in org A ---
    # Older client-visible roadmap with a mix of visible + internal items.
    s.add(Roadmap(id=1, workspace_id=WS_A, organization_id=ORG_A, diagnosis_id=1,
                  visibility="CLIENT_VISIBLE", created_at=_dt.datetime(2024, 1, 1)))
    s.add(RoadmapItem(id=10, roadmap_id=1, title="client item", dimension="Ops",
                      phase=30, status="DONE", visibility="CLIENT_VISIBLE"))
    s.add(RoadmapItem(id=11, roadmap_id=1, title="assigned item", dimension="Ops",
                      phase=30, status="TODO", visibility="CLIENT_ASSIGNED"))
    s.add(RoadmapItem(id=12, roadmap_id=1, title="hidden item", dimension="Ops",
                      phase=30, status="TODO", visibility="INTERNAL_ONLY"))

    # Org-B roadmap (cross-org probing).
    s.add(Roadmap(id=3, workspace_id=WS_B, organization_id=ORG_B, diagnosis_id=3,
                  visibility="CLIENT_VISIBLE", created_at=_dt.datetime(2024, 1, 1)))
    s.add(RoadmapItem(id=30, roadmap_id=3, title="B item", dimension="Ops",
                      phase=30, status="DONE", visibility="CLIENT_VISIBLE"))

    s.commit()


def _seed_internal_latest_roadmap(s):
    """Add a NEWER internal roadmap in org A so it becomes the 'latest'. Used by
    the test that a client must not receive an internal latest roadmap."""
    if s.query(Roadmap).filter(Roadmap.id == 2).first() is None:
        s.add(Roadmap(id=2, workspace_id=WS_A, organization_id=ORG_A, diagnosis_id=1,
                      visibility="INTERNAL_ONLY", created_at=_dt.datetime(2024, 6, 1)))
        s.add(RoadmapItem(id=20, roadmap_id=2, title="internal item", dimension="Ops",
                          phase=30, status="TODO", visibility="INTERNAL_ONLY"))
        s.commit()


# --------------------------------------------------------------------------- #
# Auth helpers
# --------------------------------------------------------------------------- #
def _headers(user_id: int, org_id: int) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org_id)}


def crew_headers(org_id: int = ORG_A) -> dict:
    return _headers(UID_CREW, org_id)


def clientA_headers(org_id: int = ORG_A) -> dict:
    return _headers(UID_A_OWNER, org_id)


# =========================================================================== #
# /api/roadmaps/latest
# =========================================================================== #

def test_roadmaps_latest_client_filters_internal_items(client):
    """A CLIENT_USER receives the client-visible latest roadmap but ONLY its
    client-visible items — the INTERNAL_ONLY item must never appear."""
    r = client.get("/api/roadmaps/latest", params={"workspace_id": WS_A},
                   headers=clientA_headers())
    assert r.status_code == 200
    body = r.json()
    assert body is not None
    titles = {it["title"] for it in body["items"]}
    assert "client item" in titles
    assert "assigned item" in titles
    assert "hidden item" not in titles
    for it in body["items"]:
        assert it["visibility"] != "INTERNAL_ONLY"


def test_roadmaps_latest_client_hides_internal_container(client, db_session):
    """When the LATEST roadmap is INTERNAL_ONLY, a client must NOT receive it
    (404) — never the internal roadmap nor its items."""
    _seed_internal_latest_roadmap(db_session)
    r = client.get("/api/roadmaps/latest", params={"workspace_id": WS_A},
                   headers=clientA_headers())
    assert r.status_code == 404


def test_roadmaps_latest_crew_sees_internal_latest(client, db_session):
    """Crew see the true latest roadmap (the internal one) and all its items."""
    _seed_internal_latest_roadmap(db_session)
    r = client.get("/api/roadmaps/latest", params={"workspace_id": WS_A},
                   headers=crew_headers())
    assert r.status_code == 200
    body = r.json()
    assert body["visibility"] == "INTERNAL_ONLY"
    titles = {it["title"] for it in body["items"]}
    assert "internal item" in titles


def test_roadmaps_latest_cross_org_not_found(client):
    """Client A pointing at org B's workspace must be rejected (membership)."""
    r = client.get("/api/roadmaps/latest", params={"workspace_id": WS_B},
                   headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


# =========================================================================== #
# /api/roadmaps/items/{id}  (PATCH)
# =========================================================================== #

def test_roadmaps_item_patch_client_cannot_touch_internal(client):
    """A client patching an INTERNAL_ONLY item gets 404 — the item is invisible
    to them, so it must behave as if it does not exist."""
    r = client.patch("/api/roadmaps/items/12", json={"status": "DONE"},
                      headers=clientA_headers())
    assert r.status_code == 404


def test_roadmaps_item_patch_client_can_touch_assigned(client):
    """A client CAN update an item assigned/visible to them (CLIENT_ASSIGNED)."""
    r = client.patch("/api/roadmaps/items/11", json={"status": "IN_PROGRESS"},
                      headers=clientA_headers())
    assert r.status_code == 200
    assert r.json()["status"] == "IN_PROGRESS"


def test_roadmaps_item_patch_crew_can_touch_internal(client):
    """Crew may update any item in scope, including internal ones."""
    r = client.patch("/api/roadmaps/items/12", json={"status": "IN_PROGRESS"},
                      headers=crew_headers())
    assert r.status_code == 200
    assert r.json()["status"] == "IN_PROGRESS"


# =========================================================================== #
# /api/diagnoses/latest
# =========================================================================== #

def test_diagnoses_latest_client_skips_internal(client):
    """Latest diagnosis for a client = the latest CLIENT_VISIBLE one (id=1),
    NOT the newer INTERNAL_ONLY one (id=2)."""
    r = client.get("/api/diagnoses/latest", params={"workspace_id": WS_A},
                   headers=clientA_headers())
    assert r.status_code == 200
    body = r.json()
    assert body is not None
    assert body["id"] == 1
    assert body["visibility"] == "CLIENT_VISIBLE"


def test_diagnoses_latest_crew_sees_internal_latest(client):
    """Crew see the true latest diagnosis — the INTERNAL_ONLY id=2."""
    r = client.get("/api/diagnoses/latest", params={"workspace_id": WS_A},
                   headers=crew_headers())
    assert r.status_code == 200
    assert r.json()["id"] == 2


def test_diagnoses_latest_cross_org_not_found(client):
    """Client A may not read org B's workspace diagnosis."""
    r = client.get("/api/diagnoses/latest", params={"workspace_id": WS_B},
                   headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


# =========================================================================== #
# /api/diagnoses/{id}
# =========================================================================== #

def test_diagnoses_detail_client_sees_visible(client):
    """A client may read a CLIENT_VISIBLE diagnosis of its org."""
    r = client.get("/api/diagnoses/1", headers=clientA_headers())
    assert r.status_code == 200
    assert r.json()["id"] == 1


def test_diagnoses_detail_client_hides_internal(client):
    """A client must NOT read an INTERNAL_ONLY diagnosis of its own org (404)."""
    r = client.get("/api/diagnoses/2", headers=clientA_headers())
    assert r.status_code == 404


def test_diagnoses_detail_crew_sees_internal(client):
    """Crew may read an internal diagnosis in scope."""
    r = client.get("/api/diagnoses/2", headers=crew_headers())
    assert r.status_code == 200
    assert r.json()["id"] == 2


def test_diagnoses_detail_cross_org_not_found(client):
    """Client A may not read org B's diagnosis (id=3); 404, never B's data."""
    # clientA cannot even enter org B (membership); and even pointing at org A
    # the id=3 belongs to B so the org filter excludes it.
    r = client.get("/api/diagnoses/3", headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)
    r2 = client.get("/api/diagnoses/3", headers=clientA_headers(ORG_A))
    assert r2.status_code == 404
