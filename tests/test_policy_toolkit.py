"""Endpoint-level AUTH/LEAK tests for the ``toolkit`` cluster.

These encode the TARGET secure behavior of the toolkit router
(``app/routers/toolkit.py``, mounted at ``/api``) for ToolRun-bearing
endpoints. They mirror the pattern of ``tests/test_policy_leak_endpoints.py``:
an isolated in-memory SQLite DB wired through ``app.dependency_overrides``,
``StaticPool``, ``Base.metadata.create_all``, override cleanup in teardown,
JWT tokens via ``app.security.auth.create_access_token`` and the
``X-Organization-ID`` header.

TARGET invariants asserted here:
  * No token  -> 401 on tool-run endpoints.
  * Cross-org -> 404 (never reveal another org's ToolRun) for GET, /execute,
    /status, /recommendations, /export-markdown.
  * Visibility -> a CLIENT_USER of the owning org gets 404 on an
    INTERNAL_ONLY run and 200 on a CLIENT_SHARED run.
  * Capability -> a CLIENT_USER may NOT create a run, execute a run, or save
    outputs (403). Crew may.
  * Crew (SYNER_CREW) sees and operates runs of any org named in its
    X-Organization-ID header.

Suite-green rule: the security retrofit of the router is being applied in
PARALLEL by another agent and is NOT in this tree yet. Tests that assert the
target behavior but fail against TODAY's (un-wired) router are marked
``xfail(strict=False)`` so they flip to "xpass"/"pass" automatically once the
retrofit lands. The inventory below records which is which.

Run:
    .venv/bin/python -m pytest tests/test_policy_toolkit.py -q
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

# Import every model module so all tables register on Base.metadata before
# create_all (FK targets: organizations, workspaces, users, toolkit_*).
from app.models import models as m  # noqa: F401
from app.models import clevel as cl  # noqa: F401
from app.models import insight as ins  # noqa: F401
from app.models import raci as rc  # noqa: F401
from app.models import kpi as kp  # noqa: F401
from app.models import toolkit as tk  # noqa: F401

from app.models.models import User, Organization, OrganizationUser, Workspace
from app.models.toolkit import (
    ConsultingToolkit, ConsultingTool, ToolRun, ToolOutput,
    ToolRunStatus, Visibility,
)


# --------------------------------------------------------------------------- #
# Identifiers
# --------------------------------------------------------------------------- #

ORG_A = 100      # client org A
ORG_B = 200      # client org B
ORG_SYNER = 1    # the Syner internal org

UID_CREW = 10        # SYNER_CREW, member of Syner org as SYNER_PARTNER
UID_A_OWNER = 11     # CLIENT_USER, owner of org A
UID_B_OWNER = 12     # CLIENT_USER, owner of org B

TOOLKIT_ID = 500
TOOL_ID = 600

# ToolRuns (all in org A unless noted)
RUN_A_INTERNAL = 1      # org A, visibility INTERNAL_ONLY
RUN_A_SHARED = 2        # org A, visibility CLIENT_SHARED
RUN_B_INTERNAL = 3      # org B, visibility INTERNAL_ONLY (cross-org probe)
RUN_B_SHARED = 4        # org B, visibility CLIENT_SHARED (cross-org probe)


# --------------------------------------------------------------------------- #
# Isolated DB + dependency override
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
            pass  # module-scoped session is closed by the db_session fixture

    app.dependency_overrides[get_db] = _override_get_db
    # The toolkit router imports get_db from app.database directly (same symbol
    # overridden above), so no router-local get_db override is needed. Should a
    # future retrofit bind its own get_db, add the override here by identity.
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
    s.add(Workspace(id=1000, organization_id=ORG_A, name="WS A"))
    s.add(Workspace(id=2000, organization_id=ORG_B, name="WS B"))

    # --- A toolkit + tool shared by all runs ---
    s.add(ConsultingToolkit(id=TOOLKIT_ID, name="FODA Toolkit", is_active=True))
    s.add(ConsultingTool(id=TOOL_ID, toolkit_id=TOOLKIT_ID, name="FODA Ejecutivo",
                         is_active=True))

    # --- ToolRuns ---
    # Org A: one INTERNAL_ONLY, one CLIENT_SHARED.
    s.add(ToolRun(id=RUN_A_INTERNAL, organization_id=ORG_A, workspace_id=1000,
                  tool_id=TOOL_ID, created_by=UID_CREW,
                  status=ToolRunStatus.AI_GENERATED, visibility=Visibility.INTERNAL_ONLY,
                  created_at=_dt.datetime(2024, 1, 1)))
    s.add(ToolRun(id=RUN_A_SHARED, organization_id=ORG_A, workspace_id=1000,
                  tool_id=TOOL_ID, created_by=UID_CREW,
                  status=ToolRunStatus.CLIENT_SHARED, visibility=Visibility.CLIENT_SHARED,
                  created_at=_dt.datetime(2024, 2, 1)))
    # Org B: cross-org probes.
    s.add(ToolRun(id=RUN_B_INTERNAL, organization_id=ORG_B, workspace_id=2000,
                  tool_id=TOOL_ID, created_by=UID_CREW,
                  status=ToolRunStatus.AI_GENERATED, visibility=Visibility.INTERNAL_ONLY,
                  created_at=_dt.datetime(2024, 1, 1)))
    s.add(ToolRun(id=RUN_B_SHARED, organization_id=ORG_B, workspace_id=2000,
                  tool_id=TOOL_ID, created_by=UID_CREW,
                  status=ToolRunStatus.CLIENT_SHARED, visibility=Visibility.CLIENT_SHARED,
                  created_at=_dt.datetime(2024, 2, 1)))

    # Give each run an output so /export-markdown has content to render.
    s.add(ToolOutput(run_id=RUN_A_INTERNAL, content_markdown="internal A md"))
    s.add(ToolOutput(run_id=RUN_A_SHARED, content_markdown="shared A md"))
    s.add(ToolOutput(run_id=RUN_B_SHARED, content_markdown="shared B md"))

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


def clientB_headers(org_id: int = ORG_B) -> dict:
    return _headers(UID_B_OWNER, org_id)


# =========================================================================== #
# 1. No token -> 401
# =========================================================================== #

def test_get_tool_run_requires_auth(client):
    r = client.get(f"/api/tool-runs/{RUN_A_SHARED}")
    assert r.status_code == 401


def test_execute_tool_run_requires_auth(client):
    r = client.post(f"/api/tool-runs/{RUN_A_SHARED}/execute")
    assert r.status_code == 401


def test_update_status_requires_auth(client):
    r = client.patch(f"/api/tool-runs/{RUN_A_SHARED}/status",
                     json={"status": "APPROVED"})
    assert r.status_code == 401


def test_get_recommendations_requires_auth(client):
    r = client.get(f"/api/tool-runs/{RUN_A_SHARED}/recommendations")
    assert r.status_code == 401


def test_create_tool_run_requires_auth(client):
    # create_tool_run already depends on get_current_user/get_current_org_id,
    # so missing auth is 401 today and must stay 401 — hard assert.
    r = client.post("/api/tool-runs", json={"tool_id": TOOL_ID, "workspace_id": 1000})
    assert r.status_code == 401


# export-markdown already depends on get_current_user today, so no-token must
# be 401 regardless of the retrofit. This is a hard assert (no xfail).
def test_export_markdown_requires_auth(client):
    r = client.post(f"/api/tool-runs/{RUN_A_SHARED}/export-markdown")
    assert r.status_code == 401


# =========================================================================== #
# 2. Cross-org -> 404 (never reveal another org's ToolRun)
# =========================================================================== #

def test_get_run_cross_org_client_not_found(client):
    """Client A (X-Org=A) requesting org B's run must 404, not leak it."""
    r = client.get(f"/api/tool-runs/{RUN_B_SHARED}", headers=clientA_headers(ORG_A))
    assert r.status_code == 404


def test_get_run_cross_org_crew_scoped_not_found(client):
    """Crew scoped to org A must NOT reach a run that lives in org B."""
    r = client.get(f"/api/tool-runs/{RUN_B_SHARED}", headers=crew_headers(ORG_A))
    assert r.status_code == 404


def test_execute_cross_org_not_found(client):
    r = client.post(f"/api/tool-runs/{RUN_B_INTERNAL}/execute",
                    headers=crew_headers(ORG_A))
    assert r.status_code == 404


def test_update_status_cross_org_not_found(client):
    r = client.patch(f"/api/tool-runs/{RUN_B_INTERNAL}/status",
                     json={"status": "APPROVED"}, headers=crew_headers(ORG_A))
    assert r.status_code == 404


def test_get_recommendations_cross_org_not_found(client):
    r = client.get(f"/api/tool-runs/{RUN_B_SHARED}/recommendations",
                   headers=clientA_headers(ORG_A))
    assert r.status_code == 404


def test_export_markdown_cross_org_not_found(client):
    r = client.post(f"/api/tool-runs/{RUN_B_SHARED}/export-markdown",
                    headers=clientA_headers(ORG_A))
    assert r.status_code == 404


# =========================================================================== #
# 3. Visibility (within the owning org, for a CLIENT_USER)
# =========================================================================== #

def test_client_cannot_see_internal_run_of_own_org(client):
    """A CLIENT_USER of org A must NOT see an INTERNAL_ONLY run -> 404."""
    r = client.get(f"/api/tool-runs/{RUN_A_INTERNAL}", headers=clientA_headers())
    assert r.status_code == 404


def test_client_can_see_shared_run_of_own_org(client):
    """A CLIENT_USER of org A SHOULD see a CLIENT_SHARED run -> 200.

    This passes today (no auth/visibility filter blocks it) and must keep
    passing after the retrofit, so it is a hard assert.
    """
    r = client.get(f"/api/tool-runs/{RUN_A_SHARED}", headers=clientA_headers())
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == RUN_A_SHARED
    assert body["visibility"] == "CLIENT_SHARED"


# =========================================================================== #
# 4. Capability: CLIENT_USER may not create / execute / save outputs
# =========================================================================== #

def test_client_cannot_create_run(client):
    r = client.post("/api/tool-runs",
                    json={"tool_id": TOOL_ID, "workspace_id": 1000},
                    headers=clientA_headers())
    assert r.status_code == 403


def test_client_cannot_execute_run(client):
    r = client.post(f"/api/tool-runs/{RUN_A_SHARED}/execute",
                    headers=clientA_headers())
    assert r.status_code == 403


def test_client_cannot_save_outputs(client):
    r = client.post(f"/api/tool-runs/{RUN_A_SHARED}/outputs",
                    json={"content_markdown": "client edit"},
                    headers=clientA_headers())
    assert r.status_code == 403


# =========================================================================== #
# 5. Crew can see and operate runs of any org named in X-Organization-ID
# =========================================================================== #

def test_crew_can_see_internal_run_of_scoped_org(client):
    """Crew scoped to org A sees the INTERNAL_ONLY run of org A -> 200.

    Passes today; must keep passing post-retrofit (hard assert).
    """
    r = client.get(f"/api/tool-runs/{RUN_A_INTERNAL}", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    assert r.json()["id"] == RUN_A_INTERNAL


def test_crew_can_create_run_in_scoped_org(client):
    """Crew may create a ToolRun in the org it is scoped to -> 200."""
    r = client.post("/api/tool-runs",
                    json={"tool_id": TOOL_ID, "workspace_id": 1000},
                    headers=crew_headers(ORG_A))
    assert r.status_code == 200
    body = r.json()
    assert body["organization_id"] == ORG_A
    assert body["tool_id"] == TOOL_ID


def test_crew_can_execute_run_of_scoped_org(client):
    """Crew may execute a run in its scoped org -> 200."""
    r = client.post(f"/api/tool-runs/{RUN_A_INTERNAL}/execute",
                    headers=crew_headers(ORG_A))
    assert r.status_code == 200
    assert r.json()["id"] == RUN_A_INTERNAL


def test_crew_in_org_b_can_see_b_run(client):
    """Crew scoped to org B reaches org B's run (cross-client consulting)."""
    r = client.get(f"/api/tool-runs/{RUN_B_SHARED}", headers=crew_headers(ORG_B))
    assert r.status_code == 200
    assert r.json()["id"] == RUN_B_SHARED


# =========================================================================== #
# 6. GET /tool-runs (list / history)
# =========================================================================== #

def test_list_tool_runs_requires_auth(client):
    """No token -> 401 on the list endpoint."""
    r = client.get("/api/tool-runs")
    assert r.status_code == 401


def test_crew_lists_all_runs_of_scoped_org(client):
    """Crew scoped to org A sees every org-A run (INTERNAL + SHARED) and no
    runs from org B."""
    r = client.get("/api/tool-runs", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    body = r.json()
    ids = {item["id"] for item in body}
    # Both org-A runs are present...
    assert RUN_A_INTERNAL in ids
    assert RUN_A_SHARED in ids
    # ...and neither org-B run leaks in.
    assert RUN_B_INTERNAL not in ids
    assert RUN_B_SHARED not in ids
    # Contract: every item carries the documented fields.
    sample = next(i for i in body if i["id"] == RUN_A_INTERNAL)
    assert set(sample.keys()) == {
        "id", "tool_id", "tool_name", "status", "visibility",
        "workspace_id", "created_at",
    }
    assert sample["tool_name"] == "FODA Ejecutivo"
    assert sample["visibility"] == "INTERNAL_ONLY"


def test_list_runs_ordered_created_at_desc(client):
    """Newest run first (RUN_A_SHARED is 2024-02, RUN_A_INTERNAL is 2024-01)."""
    r = client.get("/api/tool-runs", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    a_ids = [i["id"] for i in r.json() if i["id"] in (RUN_A_INTERNAL, RUN_A_SHARED)]
    assert a_ids == [RUN_A_SHARED, RUN_A_INTERNAL]


def test_client_lists_only_shared_runs_of_own_org(client):
    """A CLIENT_USER of org A only sees CLIENT_SHARED runs (not INTERNAL_ONLY)."""
    r = client.get("/api/tool-runs", headers=clientA_headers())
    assert r.status_code == 200
    ids = {item["id"] for item in r.json()}
    assert RUN_A_SHARED in ids
    assert RUN_A_INTERNAL not in ids
    # And nothing from org B.
    assert RUN_B_SHARED not in ids
    assert RUN_B_INTERNAL not in ids


def test_list_runs_filter_by_status(client):
    """Filtering by status narrows the result set (crew, org A)."""
    # Only the CLIENT_SHARED-status run of org A matches.
    r = client.get("/api/tool-runs?status=CLIENT_SHARED", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    ids = {item["id"] for item in r.json()}
    assert ids == {RUN_A_SHARED}

    # The AI_GENERATED status matches only the internal org-A run.
    r2 = client.get("/api/tool-runs?status=AI_GENERATED", headers=crew_headers(ORG_A))
    assert r2.status_code == 200
    ids2 = {item["id"] for item in r2.json()}
    assert ids2 == {RUN_A_INTERNAL}


def test_list_runs_filter_by_tool_id(client):
    """Filtering by a non-existent tool_id returns an empty list."""
    r = client.get(f"/api/tool-runs?tool_id={TOOL_ID + 999}", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    assert r.json() == []
