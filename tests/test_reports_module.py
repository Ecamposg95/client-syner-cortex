"""Endpoint-level tests for the Report MODULE (app/routers/reports.py).

Covers the §6 Report lifecycle endpoints added alongside the existing
/reports/executive-brief composer:
  GET  /reports                  (list, org-scoped, visibility-filtered)
  GET  /reports/{id}             (404 if not visible / not in org)
  POST /reports                  (crew, EDIT_AI_OUTPUTS; optional tool_run_ids)
  PATCH /reports/{id}            (edit + gated status transitions)
  POST /reports/{id}/export-markdown  (crew)

Mirrors tests/test_policy_toolkit.py: an isolated in-memory SQLite DB wired
through app.dependency_overrides, StaticPool, Base.metadata.create_all, JWT
tokens, and the X-Organization-ID header.

TARGET invariants:
  * crew can create a DRAFT report, approve it, and share it with the client;
  * a CLIENT_USER of the owning org sees ONLY CLIENT_SHARED reports;
  * cross-org access is 404 (never reveal another tenant's report);
  * a CLIENT_USER may NOT approve or share (403);
  * composing from tool_run_ids pulls the runs' outputs into content;
  * the pre-existing /reports/executive-brief still responds.

Run:
    .venv/bin/python -m pytest tests/test_reports_module.py -q
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

# Import every model module so all tables register on Base.metadata.
from app.models import models as m  # noqa: F401
from app.models import clevel as cl  # noqa: F401
from app.models import insight as ins  # noqa: F401
from app.models import raci as rc  # noqa: F401
from app.models import kpi as kp  # noqa: F401
from app.models import toolkit as tk  # noqa: F401
from app.models import report as rp  # noqa: F401

from app.models.models import User, Organization, OrganizationUser, Workspace
from app.models.toolkit import ConsultingToolkit, ConsultingTool, ToolRun, ToolOutput, ToolRunStatus, Visibility
from app.models.report import Report, ReportStatus


# --------------------------------------------------------------------------- #
# Identifiers
# --------------------------------------------------------------------------- #

ORG_SYNER = 1
ORG_A = 100
ORG_B = 200

UID_CREW = 10
UID_A_OWNER = 11
UID_B_OWNER = 12

WS_A = 1000
WS_B = 2000

TOOLKIT_ID = 500
TOOL_ID = 600
RUN_A = 700           # a tool run in org A with an output (for composition)
RUN_B = 701           # a tool run in org B (cross-org composition probe)

REP_A_DRAFT = 1       # org A, DRAFT_INTERNAL
REP_A_SHARED = 2      # org A, CLIENT_SHARED
REP_B_SHARED = 3      # org B, CLIENT_SHARED (cross-org probe)


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
    s.add(Workspace(id=WS_A, organization_id=ORG_A, name="WS A"))
    s.add(Workspace(id=WS_B, organization_id=ORG_B, name="WS B"))

    # A tool + runs with outputs for the composition test.
    s.add(ConsultingToolkit(id=TOOLKIT_ID, name="FODA Toolkit", is_active=True))
    s.add(ConsultingTool(id=TOOL_ID, toolkit_id=TOOLKIT_ID, name="FODA Ejecutivo", is_active=True))
    s.add(ToolRun(id=RUN_A, organization_id=ORG_A, workspace_id=WS_A, tool_id=TOOL_ID,
                  created_by=UID_CREW, status=ToolRunStatus.AI_GENERATED,
                  visibility=Visibility.INTERNAL_ONLY, created_at=_dt.datetime(2024, 1, 1)))
    s.add(ToolRun(id=RUN_B, organization_id=ORG_B, workspace_id=WS_B, tool_id=TOOL_ID,
                  created_by=UID_CREW, status=ToolRunStatus.AI_GENERATED,
                  visibility=Visibility.INTERNAL_ONLY, created_at=_dt.datetime(2024, 1, 1)))
    s.add(ToolOutput(run_id=RUN_A, content_markdown="## FODA\nFortalezas: equipo"))

    # Pre-seeded reports.
    s.add(Report(id=REP_A_DRAFT, organization_id=ORG_A, workspace_id=WS_A,
                 created_by=UID_CREW, title="Borrador A", report_type="DIAG",
                 status=ReportStatus.DRAFT_INTERNAL, visibility="DRAFT_INTERNAL",
                 content={"x": 1}, created_at=_dt.datetime(2024, 1, 1)))
    s.add(Report(id=REP_A_SHARED, organization_id=ORG_A, workspace_id=WS_A,
                 created_by=UID_CREW, title="Compartido A", report_type="DIAG",
                 status=ReportStatus.CLIENT_SHARED, visibility="CLIENT_SHARED",
                 content={"x": 2}, created_at=_dt.datetime(2024, 2, 1)))
    s.add(Report(id=REP_B_SHARED, organization_id=ORG_B, workspace_id=WS_B,
                 created_by=UID_CREW, title="Compartido B", report_type="DIAG",
                 status=ReportStatus.CLIENT_SHARED, visibility="CLIENT_SHARED",
                 content={"x": 3}, created_at=_dt.datetime(2024, 2, 1)))
    s.commit()


def _headers(user_id: int, org_id: int) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org_id)}


def crew_headers(org_id=ORG_A):
    return _headers(UID_CREW, org_id)


def clientA_headers(org_id=ORG_A):
    return _headers(UID_A_OWNER, org_id)


def clientB_headers(org_id=ORG_B):
    return _headers(UID_B_OWNER, org_id)


# =========================================================================== #
# Auth
# =========================================================================== #

def test_list_requires_auth(client):
    assert client.get("/api/reports").status_code == 401


# =========================================================================== #
# Listing & visibility
# =========================================================================== #

def test_crew_lists_all_reports_in_org(client):
    r = client.get("/api/reports", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    ids = {row["id"] for row in r.json()}
    # Crew sees both the draft and the shared report of org A.
    assert REP_A_DRAFT in ids and REP_A_SHARED in ids
    # ...and never another org's report.
    assert REP_B_SHARED not in ids


def test_client_lists_only_client_shared(client):
    r = client.get("/api/reports", headers=clientA_headers())
    assert r.status_code == 200
    ids = {row["id"] for row in r.json()}
    assert ids == {REP_A_SHARED}  # only the CLIENT_SHARED report of its org


def test_list_status_filter(client):
    r = client.get("/api/reports?status_filter=CLIENT_SHARED", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    assert {row["id"] for row in r.json()} == {REP_A_SHARED}


# =========================================================================== #
# Detail / cross-org / visibility 404s
# =========================================================================== #

def test_client_cannot_see_internal_report(client):
    r = client.get(f"/api/reports/{REP_A_DRAFT}", headers=clientA_headers())
    assert r.status_code == 404


def test_client_can_see_shared_report(client):
    r = client.get(f"/api/reports/{REP_A_SHARED}", headers=clientA_headers())
    assert r.status_code == 200
    assert r.json()["id"] == REP_A_SHARED


def test_cross_org_report_not_found(client):
    r = client.get(f"/api/reports/{REP_B_SHARED}", headers=clientA_headers(ORG_A))
    assert r.status_code == 404


def test_crew_scoped_cross_org_not_found(client):
    r = client.get(f"/api/reports/{REP_B_SHARED}", headers=crew_headers(ORG_A))
    assert r.status_code == 404


# =========================================================================== #
# Create
# =========================================================================== #

def test_client_cannot_create_report(client):
    r = client.post("/api/reports", json={"title": "Nope"}, headers=clientA_headers())
    assert r.status_code == 403


def test_crew_creates_draft_report(client):
    r = client.post("/api/reports",
                    json={"title": "Nuevo", "report_type": "DIAG", "workspace_id": WS_A},
                    headers=crew_headers(ORG_A))
    assert r.status_code == 200
    body = r.json()
    assert body["organization_id"] == ORG_A
    assert body["status"] == "DRAFT_INTERNAL"
    assert body["visibility"] == "DRAFT_INTERNAL"


def test_crew_creates_report_composed_from_tool_runs(client):
    r = client.post("/api/reports",
                    json={"title": "Compuesto", "tool_run_ids": [RUN_A]},
                    headers=crew_headers(ORG_A))
    assert r.status_code == 200
    content = r.json()["content"]
    assert content["composed_from_tool_runs"] == [RUN_A]
    assert content["sections"][0]["outputs"][0]["content_markdown"].startswith("## FODA")


def test_compose_from_cross_org_run_rejected(client):
    """Composing from a run in another org must 404 (never compose cross-tenant)."""
    r = client.post("/api/reports",
                    json={"title": "Bad", "tool_run_ids": [RUN_B]},
                    headers=crew_headers(ORG_A))
    assert r.status_code == 404


# =========================================================================== #
# Lifecycle: approve -> share (gated)
# =========================================================================== #

def test_client_cannot_approve(client):
    r = client.patch(f"/api/reports/{REP_A_DRAFT}", json={"status": "APPROVED"},
                     headers=clientA_headers())
    assert r.status_code == 403


def test_client_cannot_share(client):
    r = client.patch(f"/api/reports/{REP_A_DRAFT}", json={"status": "CLIENT_SHARED"},
                     headers=clientA_headers())
    assert r.status_code == 403


def test_crew_full_lifecycle_approve_then_share(client):
    # Create a fresh draft to drive through the lifecycle.
    created = client.post("/api/reports", json={"title": "Ciclo"},
                          headers=crew_headers(ORG_A)).json()
    rid = created["id"]

    appr = client.patch(f"/api/reports/{rid}", json={"status": "APPROVED"},
                        headers=crew_headers(ORG_A))
    assert appr.status_code == 200
    assert appr.json()["status"] == "APPROVED"
    assert appr.json()["approved_by"] == UID_CREW

    shared = client.patch(f"/api/reports/{rid}", json={"status": "CLIENT_SHARED"},
                          headers=crew_headers(ORG_A))
    assert shared.status_code == 200
    body = shared.json()
    assert body["status"] == "CLIENT_SHARED"
    assert body["visibility"] == "CLIENT_SHARED"
    assert body["shared_at"] is not None

    # The client of org A can now see it.
    seen = client.get(f"/api/reports/{rid}", headers=clientA_headers())
    assert seen.status_code == 200


def test_crew_can_edit_title_and_content(client):
    r = client.patch(f"/api/reports/{REP_A_DRAFT}",
                     json={"title": "Borrador A v2", "content": {"x": 99}},
                     headers=crew_headers(ORG_A))
    assert r.status_code == 200
    assert r.json()["title"] == "Borrador A v2"
    assert r.json()["content"] == {"x": 99}


# =========================================================================== #
# Export
# =========================================================================== #

def test_crew_export_markdown(client):
    r = client.post(f"/api/reports/{REP_A_SHARED}/export-markdown", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    assert "# Compartido A" in r.json()["markdown"]


def test_client_cannot_export(client):
    r = client.post(f"/api/reports/{REP_A_SHARED}/export-markdown", headers=clientA_headers())
    assert r.status_code == 403


# =========================================================================== #
# The pre-existing executive-brief endpoint still responds (not shadowed)
# =========================================================================== #

def test_executive_brief_still_routes(client):
    """The /reports/executive-brief endpoint must not be shadowed by the new
    GET /reports/{id} path param. It needs a workspace_id query param; with a
    workspace that has no diagnosis it returns 400 (its own 'no diagnosis'
    response) — crucially NOT a 404 from the {id} route or a routing error."""
    r = client.get(f"/api/reports/executive-brief?workspace_id={WS_A}",
                   headers=crew_headers(ORG_A))
    assert r.status_code == 400
    assert "diagnosis" in r.json()["detail"].lower()
