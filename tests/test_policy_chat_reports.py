"""Endpoint-level policy tests for the CHAT and REPORTS routers (Fase 3 wiring).

INVARIANT (Task Pack §4): a CLIENT_USER must NEVER reach, through any HTTP
endpoint, (a) another organization's data, nor (b) internal-state material of
its own org. Crew (SYNER_CREW) sees everything within its scope.

These tests hit the REAL endpoints through FastAPI's TestClient against an
isolated in-memory SQLite DB (the dev database is never touched). Pattern mirrors
tests/test_policy_leak_endpoints.py: dependency_overrides[get_db], JWT tokens and
the X-Organization-ID header.

Covered surfaces:
  - /api/chat/* — internal crew tool, gated on USE_INTERNAL_RAG. Clients get 403;
    cross-org sessions 404; crew works.
  - /api/reports/executive-brief — gated on VIEW_APPROVED_REPORTS, brief composed
    only from client-visible diagnosis/roadmap for clients; cross-org 404.

Run:
    .venv/bin/python -m pytest tests/test_policy_chat_reports.py -q
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

# Register every model module on Base.metadata before create_all.
from app.models import models as m  # noqa: F401
from app.models import clevel as cl  # noqa: F401
from app.models import insight as ins  # noqa: F401
from app.models import raci as rc  # noqa: F401
from app.models import kpi as kp  # noqa: F401
from app.models import toolkit as tk  # noqa: F401

from app.models.models import (
    User, Organization, OrganizationUser, Workspace,
    ChatSession, ChatMessage,
    Diagnosis, DiagnosisDimension, Roadmap, RoadmapItem,
)

# --------------------------------------------------------------------------- #
# Ids
# --------------------------------------------------------------------------- #
ORG_A = 100        # client org A
ORG_B = 200        # client org B
ORG_SYNER = 1      # Syner internal org

UID_CREW = 10
UID_A_OWNER = 11
UID_B_OWNER = 12

WS_A = 1000        # workspace in org A
WS_B = 2000        # workspace in org B


# --------------------------------------------------------------------------- #
# Isolated DB + overrides
# --------------------------------------------------------------------------- #
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

    # --- Chat sessions (all INTERNAL_ONLY by design): one in A, one in B ---
    s.add(ChatSession(id=1, workspace_id=WS_A, organization_id=ORG_A, user_id=UID_CREW,
                      title="crew session A", visibility="INTERNAL_ONLY"))
    s.add(ChatMessage(id=1, session_id=1, sender="user", content="internal A",
                      visibility="INTERNAL_ONLY"))
    s.add(ChatSession(id=2, workspace_id=WS_B, organization_id=ORG_B, user_id=UID_CREW,
                      title="crew session B", visibility="INTERNAL_ONLY"))

    # --- Diagnoses in org A: a CLIENT_VISIBLE (older) and an INTERNAL_ONLY (latest) ---
    s.add(Diagnosis(id=1, workspace_id=WS_A, organization_id=ORG_A, user_id=UID_CREW,
                    status="COMPLETED", visibility="CLIENT_VISIBLE",
                    created_at=_dt.datetime(2024, 1, 1)))
    s.add(DiagnosisDimension(id=1, diagnosis_id=1, name="Ventas", rating=3,
                             findings="client finding", recommendations="client rec"))
    # Latest diagnosis is INTERNAL_ONLY — a client must NOT compose a brief from it.
    s.add(Diagnosis(id=2, workspace_id=WS_A, organization_id=ORG_A, user_id=UID_CREW,
                    status="COMPLETED", visibility="INTERNAL_ONLY",
                    created_at=_dt.datetime(2024, 6, 1)))
    s.add(DiagnosisDimension(id=2, diagnosis_id=2, name="Ventas", rating=2,
                             findings="INTERNAL finding", recommendations="INTERNAL rec"))

    # Org B diagnosis (cross-org probe target)
    s.add(Diagnosis(id=3, workspace_id=WS_B, organization_id=ORG_B, user_id=UID_CREW,
                    status="COMPLETED", visibility="CLIENT_VISIBLE",
                    created_at=_dt.datetime(2024, 1, 1)))
    s.add(DiagnosisDimension(id=3, diagnosis_id=3, name="Ops", rating=4,
                             findings="B finding", recommendations="B rec"))

    # --- Roadmaps in org A: client-visible roadmap with a mix of items ---
    s.add(Roadmap(id=1, workspace_id=WS_A, organization_id=ORG_A, diagnosis_id=1,
                  visibility="CLIENT_VISIBLE", created_at=_dt.datetime(2024, 1, 2)))
    s.add(RoadmapItem(id=1, roadmap_id=1, title="client item", dimension="Ops",
                      phase=30, status="DONE", visibility="CLIENT_VISIBLE"))
    s.add(RoadmapItem(id=2, roadmap_id=1, title="INTERNAL item", dimension="Ops",
                      phase=30, status="TODO", visibility="INTERNAL_ONLY"))
    # A NEWER internal-only roadmap; the client must not compose from it.
    s.add(Roadmap(id=2, workspace_id=WS_A, organization_id=ORG_A, diagnosis_id=1,
                  visibility="INTERNAL_ONLY", created_at=_dt.datetime(2024, 7, 1)))
    s.add(RoadmapItem(id=3, roadmap_id=2, title="INTERNAL latest item", dimension="Ops",
                      phase=60, status="TODO", visibility="INTERNAL_ONLY"))

    s.commit()


# --------------------------------------------------------------------------- #
# Auth helpers
# --------------------------------------------------------------------------- #
def _headers(user_id: int, org_id: int) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org_id)}


def crew_headers(org_id: int) -> dict:
    return _headers(UID_CREW, org_id)


def clientA_headers(org_id: int = ORG_A) -> dict:
    return _headers(UID_A_OWNER, org_id)


# =========================================================================== #
# CHAT — auth required
# =========================================================================== #
def test_chat_sessions_requires_auth(client):
    """No token -> 401 (no anonymous access to the internal chat tool)."""
    r = client.get("/api/chat/sessions", params={"workspace_id": WS_A},
                   headers={"X-Organization-ID": str(ORG_A)})
    assert r.status_code == 401


def test_chat_post_message_requires_auth(client):
    r = client.post("/api/chat/sessions/1/messages", json={"content": "hi"},
                    headers={"X-Organization-ID": str(ORG_A)})
    assert r.status_code == 401


# =========================================================================== #
# CHAT — CLIENT_USER is denied the internal tool (USE_INTERNAL_RAG -> 403)
# =========================================================================== #
def test_chat_list_sessions_client_forbidden(client):
    """A CLIENT_USER may not use the internal chat tool at all -> 403."""
    r = client.get("/api/chat/sessions", params={"workspace_id": WS_A},
                   headers=clientA_headers())
    assert r.status_code == 403


def test_chat_read_messages_client_forbidden(client):
    """Client must not read internal session messages -> 403 (never 200)."""
    r = client.get("/api/chat/sessions/1/messages", headers=clientA_headers())
    assert r.status_code == 403


def test_chat_create_session_client_forbidden(client):
    r = client.post("/api/chat/sessions", params={"workspace_id": WS_A},
                    json={"title": "client try"}, headers=clientA_headers())
    assert r.status_code == 403


def test_chat_post_message_client_forbidden(client):
    r = client.post("/api/chat/sessions/1/messages", json={"content": "leak?"},
                    headers=clientA_headers())
    assert r.status_code == 403


# =========================================================================== #
# CHAT — crew works, and cross-org is 404 (not 403, never confirm existence)
# =========================================================================== #
def test_chat_list_sessions_crew_ok(client):
    r = client.get("/api/chat/sessions", params={"workspace_id": WS_A},
                   headers=crew_headers(ORG_A))
    assert r.status_code == 200
    titles = {s["title"] for s in r.json()}
    assert "crew session A" in titles


def test_chat_read_messages_crew_ok(client):
    r = client.get("/api/chat/sessions/1/messages", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    contents = {msg["content"] for msg in r.json()}
    assert "internal A" in contents


def test_chat_session_cross_org_not_found(client):
    """Crew scoped to ORG_A must not reach ORG_B's session id=2 -> 404."""
    r = client.get("/api/chat/sessions/2/messages", headers=crew_headers(ORG_A))
    assert r.status_code == 404


def test_chat_create_session_crew_ok(client):
    r = client.post("/api/chat/sessions", params={"workspace_id": WS_A},
                    json={"title": "fresh crew session"}, headers=crew_headers(ORG_A))
    assert r.status_code == 201
    body = r.json()
    assert body["visibility"] == "INTERNAL_ONLY"
    assert body["organization_id"] == ORG_A


# =========================================================================== #
# REPORTS — auth required
# =========================================================================== #
def test_reports_brief_requires_auth(client):
    r = client.get("/api/reports/executive-brief", params={"workspace_id": WS_A},
                   headers={"X-Organization-ID": str(ORG_A)})
    assert r.status_code == 401


# =========================================================================== #
# REPORTS — cross-org is rejected
# =========================================================================== #
def test_reports_brief_cross_org_not_found(client):
    """Client A pointing at org B's workspace must be rejected (membership/org)."""
    r = client.get("/api/reports/executive-brief", params={"workspace_id": WS_B},
                   headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


# =========================================================================== #
# REPORTS — client brief excludes internal material
# =========================================================================== #
def test_reports_brief_client_excludes_internal_diagnosis(client):
    """The client brief composes from the latest CLIENT-VISIBLE diagnosis (id=1),
    never from the newer INTERNAL_ONLY one (id=2). Internal findings must not
    appear."""
    r = client.get("/api/reports/executive-brief", params={"workspace_id": WS_A},
                   headers=clientA_headers())
    assert r.status_code == 200
    body = r.json()
    findings = {d["findings"] for d in body["dimensions"]}
    assert "client finding" in findings
    assert "INTERNAL finding" not in findings


def test_reports_brief_client_excludes_internal_roadmap_items(client):
    """The client brief must drop INTERNAL_ONLY roadmap items and must not
    compose from the newer INTERNAL_ONLY roadmap (id=2)."""
    r = client.get("/api/reports/executive-brief", params={"workspace_id": WS_A},
                   headers=clientA_headers())
    assert r.status_code == 200
    titles = {it["title"] for it in body_items(r)}
    assert "client item" in titles
    assert "INTERNAL item" not in titles
    assert "INTERNAL latest item" not in titles


def body_items(response):
    return response.json()["roadmap"]["items"]


# =========================================================================== #
# REPORTS — crew sees the full (internal) brief
# =========================================================================== #
def test_reports_brief_crew_sees_internal(client):
    """Crew composes from the latest diagnosis (the INTERNAL_ONLY id=2) and the
    latest roadmap (INTERNAL_ONLY id=2), with internal items intact."""
    r = client.get("/api/reports/executive-brief", params={"workspace_id": WS_A},
                   headers=crew_headers(ORG_A))
    assert r.status_code == 200
    body = r.json()
    findings = {d["findings"] for d in body["dimensions"]}
    assert "INTERNAL finding" in findings
    titles = {it["title"] for it in body["roadmap"]["items"]}
    assert "INTERNAL latest item" in titles
