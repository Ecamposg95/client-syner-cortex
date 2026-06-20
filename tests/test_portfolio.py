"""Tests for the Command Center / Boardroom portfolio aggregation endpoint.

GET /api/portfolio/summary is CREW-ONLY (gated by get_current_syner_crew). It
aggregates cross-org: crew sees the health of EVERY client. These tests run on an
isolated in-memory SQLite DB (StaticPool) so the dev database is never touched,
following the pattern of tests/test_policy_leak_endpoints.py.

Run:
    .venv/bin/python -m pytest tests/test_portfolio.py -q
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.security.auth import create_access_token

# Import every model module so all tables register on Base.metadata before
# create_all (the portfolio router touches clevel + insight tables).
from app.models import models as m  # noqa: F401
from app.models import clevel as cl  # noqa: F401
from app.models import insight as ins  # noqa: F401
from app.models import raci as rc  # noqa: F401
from app.models import kpi as kp  # noqa: F401
from app.models import toolkit as tk  # noqa: F401

from app.models.models import (
    User, Organization, OrganizationUser, Workspace, Module, OrganizationModule,
)
from app.models.clevel import (
    ConsultingEngagement, Finding, Decision,
    EngagementStatus, FindingCriticality, DecisionStatus,
)
from app.models.insight import (
    Insight, InsightImpact, InsightEffort, InsightStatus, InsightSource,
)

# Org ids
ORG_SYNER = 1
ORG_A = 100
ORG_B = 200

# User ids
UID_CREW = 10
UID_A_OWNER = 11


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

    # The portfolio router is wired into main.py by the orchestrator (out of this
    # task's scope). Register it here for the test if it isn't mounted yet, taking
    # care to insert it BEFORE the SPA catch-all route ("/{catchall:path}") that
    # main.py appends last — otherwise the catch-all shadows it and we get a 404.
    from app.routers import portfolio as portfolio_router
    summary_path = "/api/portfolio/summary"
    added_paths = set()
    if not any(getattr(r, "path", "") == summary_path for r in app.routes):
        before = list(app.router.routes)
        app.include_router(portfolio_router.router, prefix="/api")
        new_routes = [r for r in app.router.routes if r not in before]
        added_paths = {getattr(r, "path", "") for r in new_routes}
        # Re-order: drop the SPA catch-all to the very end so concrete API routes win.
        def _is_catchall(r):
            return getattr(r, "path", "") == "/{catchall:path}"
        app.router.routes.sort(key=_is_catchall)

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    # Remove the portfolio routes we injected so the shared `app` object stays
    # clean for any other test module that imports it.
    if added_paths:
        app.router.routes[:] = [
            r for r in app.router.routes if getattr(r, "path", "") not in added_paths
        ]


def _seed(s):
    # Organizations: one SYNER (internal, not a client) + two CLIENT orgs.
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
    ])

    s.add_all([
        OrganizationUser(organization_id=ORG_SYNER, user_id=UID_CREW, role="SYNER_PARTNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_OWNER, role="CLIENT_OWNER"),
    ])

    # Org A: 1 workspace, 1 enabled + 1 disabled module, 1 engagement w/ 2
    # findings, 2 insights, 1 PENDING + 1 APPROVED decision.
    s.add(Workspace(id=1000, organization_id=ORG_A, name="WS A"))

    s.add_all([
        Module(id=1, code="DIAG", name="Diagnosis"),
        Module(id=2, code="ROAD", name="Roadmap"),
    ])
    s.add(OrganizationModule(organization_id=ORG_A, module_id=1, is_enabled=True))
    s.add(OrganizationModule(organization_id=ORG_A, module_id=2, is_enabled=False))

    s.add(ConsultingEngagement(id=1, organization_id=ORG_A, title="Eng A",
                               status=EngagementStatus.ACTIVE))
    s.add(Finding(id=1, engagement_id=1, title="Finding A1",
                  criticality=FindingCriticality.HIGH))
    s.add(Finding(id=2, engagement_id=1, title="Finding A2",
                  criticality=FindingCriticality.MEDIUM))

    s.add(Insight(id=1, organization_id=ORG_A, title="Insight A1",
                  impact=InsightImpact.HIGH, effort=InsightEffort.LOW,
                  priority_score=9.0, quadrant="QUICK_WIN", status=InsightStatus.NEW,
                  source_type=InsightSource.MANUAL))
    s.add(Insight(id=2, organization_id=ORG_A, title="Insight A2",
                  impact=InsightImpact.MEDIUM, effort=InsightEffort.MEDIUM,
                  priority_score=5.0, quadrant="INCREMENTAL", status=InsightStatus.NEW,
                  source_type=InsightSource.MANUAL))

    s.add(Decision(id=1, organization_id=ORG_A, title="Decision A (pending)",
                   status=DecisionStatus.PENDING))
    s.add(Decision(id=2, organization_id=ORG_A, title="Decision A (approved)",
                   status=DecisionStatus.APPROVED))

    # Org B: minimal — 1 engagement, no findings/insights, 1 pending decision.
    s.add(ConsultingEngagement(id=2, organization_id=ORG_B, title="Eng B",
                               status=EngagementStatus.ACTIVE))
    s.add(Decision(id=3, organization_id=ORG_B, title="Decision B (pending)",
                   status=DecisionStatus.PENDING))

    s.commit()


def _headers(user_id: int) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Crew access
# --------------------------------------------------------------------------- #

def test_summary_crew_gets_totals_and_clients(client):
    """Crew receives the portfolio summary with totals and a per-client list."""
    r = client.get("/api/portfolio/summary", headers=_headers(UID_CREW))
    assert r.status_code == 200
    body = r.json()

    assert "totals" in body and "clients" in body

    totals = body["totals"]
    # Two CLIENT orgs (the SYNER org is excluded).
    assert totals["client_count"] == 2
    # Cross-org sums: A has 2 engagements? No — A=1, B=1 → 2 total.
    assert totals["engagement_count"] == 2
    assert totals["finding_count"] == 2          # both in org A
    assert totals["insight_count"] == 2          # both in org A
    assert totals["pending_decision_count"] == 2  # one per client (A + B)
    assert totals["enabled_module_count"] == 1   # only A's enabled module

    clients = {c["name"]: c for c in body["clients"]}
    assert set(clients) == {"Client A", "Client B"}

    a = clients["Client A"]
    assert a["user_count"] == 1
    assert a["workspace_count"] == 1
    assert a["enabled_module_count"] == 1
    assert a["engagement_count"] == 1
    assert a["finding_count"] == 2
    assert a["insight_count"] == 2
    assert a["pending_decision_count"] == 1   # the APPROVED one is excluded

    b = clients["Client B"]
    assert b["engagement_count"] == 1
    assert b["finding_count"] == 0
    assert b["insight_count"] == 0
    assert b["pending_decision_count"] == 1


# --------------------------------------------------------------------------- #
# Crew-only gate
# --------------------------------------------------------------------------- #

def test_summary_client_user_forbidden(client):
    """A CLIENT_USER must be rejected with 403 (get_current_syner_crew)."""
    r = client.get("/api/portfolio/summary", headers=_headers(UID_A_OWNER))
    assert r.status_code == 403


def test_summary_unauthenticated_rejected(client):
    """No token → 401, never an anonymous portfolio dump."""
    r = client.get("/api/portfolio/summary")
    assert r.status_code == 401
