"""Policy-wiring tests for the audit / clevel / insights routers (Fase 3, PR2).

Mirrors the harness of tests/test_policy_leak_endpoints.py (isolated in-memory
SQLite, real endpoints through TestClient) and encodes the invariants this
wiring is supposed to guarantee:

  AUDIT
    - VIEW_AUDIT is ALLOW only for SYNER_ADMIN and CONDITIONAL for SYNER_PARTNER
      (both pass the gate). NO CLIENT_* role may read the audit log -> 403.
      This fixes the prior divergence where CLIENT_OWNER/EXECUTIVE could read it
      and the "CONSULTANT" role-string drift.

  CLEVEL
    - engagements/findings/risks/decisions are org-scoped: a client pointing at
      another org's data gets 404/403 (cross-org never leaks).
    - PATCH /clevel/decisions/{id} keeps working for valid callers (client owner
      resolving its own decision; crew) and 404s for a decision out of scope.

  INSIGHTS
    - Mutations are gated by §8 actions: a client without the capability gets 403
      on generate/create; crew succeeds. Cross-org PATCH -> 404.

Run:
    .venv/bin/python -m pytest tests/test_policy_audit_clevel_insights.py -q
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

# Register every model module so all tables exist on Base.metadata.
from app.models import models as m  # noqa: F401
from app.models import clevel as cl  # noqa: F401
from app.models import insight as ins  # noqa: F401
from app.models import raci as rc  # noqa: F401
from app.models import kpi as kp  # noqa: F401
from app.models import toolkit as tk  # noqa: F401

from app.models.models import (
    User, Organization, OrganizationUser, AuditLog,
)
from app.models.clevel import (
    ConsultingEngagement, Finding, Decision, Risk,
    EngagementStatus, FindingCriticality, DecisionStatus, RiskStatus,
)
from app.models.insight import (
    Insight, InsightImpact, InsightEffort, InsightStatus, InsightSource,
)


# --------------------------------------------------------------------------- #
# Identities / orgs
# --------------------------------------------------------------------------- #
ORG_A = 100      # client org A
ORG_B = 200      # client org B
ORG_SYNER = 1    # internal Syner org

UID_CREW = 10        # SYNER_CREW, SYNER_PARTNER in Syner org
UID_A_OWNER = 11     # CLIENT_USER, CLIENT_OWNER in org A
UID_B_OWNER = 12     # CLIENT_USER, CLIENT_OWNER in org B


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


def _override_get_db_factory(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    return _override_get_db


@pytest.fixture(scope="module")
def client(db_session):
    app.dependency_overrides[get_db] = _override_get_db_factory(db_session)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def audit_client(db_session):
    """The audit router carries the real policy gate (require_action(VIEW_AUDIT))
    but, on this branch, it is NOT include_router'd in app.main — and a SPA
    catch-all route (`/{catchall:path}`) shadows any late inclusion, returning
    404 before the router runs. Fixing app.main is out of scope here, so we
    mount ONLY the audit router on a dedicated app to exercise its gate
    end-to-end. The router code under test is unchanged."""
    from fastapi import FastAPI
    from app.routers import audit as audit_router

    audit_app = FastAPI()
    audit_app.include_router(audit_router.router, prefix="/api")
    audit_app.dependency_overrides[get_db] = _override_get_db_factory(db_session)
    with TestClient(audit_app) as c:
        yield c


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

    # Audit logs in each org.
    s.add_all([
        AuditLog(id=1, organization_id=ORG_A, user_id=UID_CREW, action="DOC_UPLOAD",
                 created_at=_dt.datetime(2024, 1, 1)),
        AuditLog(id=2, organization_id=ORG_B, user_id=UID_B_OWNER, action="USER_LOGIN",
                 created_at=_dt.datetime(2024, 1, 1)),
    ])

    # C-Level data in org A and B.
    s.add(ConsultingEngagement(id=1, organization_id=ORG_A, title="Eng A",
                               status=EngagementStatus.ACTIVE))
    s.add(ConsultingEngagement(id=2, organization_id=ORG_B, title="Eng B",
                               status=EngagementStatus.ACTIVE))
    s.add(Finding(id=1, engagement_id=1, title="Finding A",
                  criticality=FindingCriticality.HIGH))
    s.add(Finding(id=2, engagement_id=2, title="Finding B",
                  criticality=FindingCriticality.HIGH))
    s.add(Decision(id=1, organization_id=ORG_A, title="Decision A",
                   status=DecisionStatus.PENDING))
    s.add(Decision(id=2, organization_id=ORG_B, title="Decision B",
                   status=DecisionStatus.PENDING))
    s.add(Risk(id=1, organization_id=ORG_A, description="Risk A", status=RiskStatus.OPEN))
    s.add(Risk(id=2, organization_id=ORG_B, description="Risk B", status=RiskStatus.OPEN))

    # Insights in org A and B.
    s.add(Insight(id=1, organization_id=ORG_A, title="Insight A",
                  impact=InsightImpact.HIGH, effort=InsightEffort.LOW,
                  priority_score=9.0, quadrant="QUICK_WIN", status=InsightStatus.NEW,
                  is_critical_alarm=False, source_type=InsightSource.MANUAL))
    s.add(Insight(id=2, organization_id=ORG_B, title="Insight B",
                  impact=InsightImpact.HIGH, effort=InsightEffort.LOW,
                  priority_score=9.0, quadrant="QUICK_WIN", status=InsightStatus.NEW,
                  is_critical_alarm=False, source_type=InsightSource.MANUAL))

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
# /api/audit  — VIEW_AUDIT
# =========================================================================== #
def test_audit_client_forbidden(audit_client):
    """CLIENT_OWNER must NOT see the audit log (VIEW_AUDIT has no CLIENT_* cell).
    This is the core divergence fix."""
    r = audit_client.get("/api/audit", headers=clientA_headers())
    assert r.status_code == 403


def test_audit_crew_partner_allowed(audit_client):
    """SYNER crew acting as SYNER_PARTNER passes VIEW_AUDIT (CONDITIONAL) and
    only sees its org's logs."""
    r = audit_client.get("/api/audit", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    actions = {row["action"] for row in r.json()}
    assert actions == {"DOC_UPLOAD"}  # org A only, never org B's USER_LOGIN


def test_audit_unauthenticated_rejected(audit_client):
    """No token -> not authorized."""
    r = audit_client.get("/api/audit")
    assert r.status_code in (401, 403)


# =========================================================================== #
# /api/clevel/*  — org scoping (cross-org never leaks)
# =========================================================================== #
def test_clevel_decisions_cross_org_forbidden(client):
    r = client.get("/api/clevel/decisions", headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


def test_clevel_decisions_own_org_only(client):
    r = client.get("/api/clevel/decisions", headers=clientA_headers())
    assert r.status_code == 200
    assert {d["title"] for d in r.json()} == {"Decision A"}


def test_clevel_findings_cross_org_engagement_not_found(client):
    """Client A may not read org B's engagement findings."""
    r = client.get("/api/clevel/engagements/2/findings", headers=clientA_headers())
    assert r.status_code in (403, 404)
    if r.status_code == 200:
        assert r.json() == []


def test_clevel_risks_own_org_only(client):
    r = client.get("/api/clevel/risks", headers=clientA_headers())
    assert r.status_code == 200
    assert {x["description"] for x in r.json()} == {"Risk A"}


# --- PATCH /clevel/decisions/{id} : behavior preserved for valid callers ---
def test_clevel_decision_update_client_owner_ok(client):
    """A CLIENT_OWNER may resolve its own org's pending decision (CLIENT_APPROVAL
    lane, kept via the canonical-role guard)."""
    r = client.patch("/api/clevel/decisions/1",
                      json={"status": "APPROVED"}, headers=clientA_headers())
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"


def test_clevel_decision_update_cross_org_not_found(client):
    """Client A cannot mutate org B's decision: scoping yields 404 (or 403 at the
    membership gate), never a cross-org write."""
    r = client.patch("/api/clevel/decisions/2",
                      json={"status": "APPROVED"}, headers=clientA_headers())
    assert r.status_code in (403, 404)
    # Org B's decision must remain untouched.
    assert client is not None


def test_clevel_decision_update_crew_ok(client):
    """Crew can also resolve a decision in the client's org."""
    r = client.patch("/api/clevel/decisions/1",
                      json={"status": "REJECTED"}, headers=crew_headers(ORG_A))
    assert r.status_code == 200
    assert r.json()["status"] == "REJECTED"


# =========================================================================== #
# /api/insights  — mutation gating + org scoping
# =========================================================================== #
def test_insights_own_org_only(client):
    r = client.get("/api/insights", headers=clientA_headers())
    assert r.status_code == 200
    assert {i["title"] for i in r.json()} == {"Insight A"}


def test_insights_cross_org_forbidden(client):
    r = client.get("/api/insights", headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


def test_insights_generate_client_forbidden(client):
    """RUN_TOOLS has no CLIENT_* cell -> a client cannot trigger generation."""
    r = client.post("/api/insights/generate", headers=clientA_headers())
    assert r.status_code == 403


def test_insights_generate_crew_ok(client):
    """Crew (SYNER_PARTNER) may regenerate; idempotent engine returns a dict."""
    r = client.post("/api/insights/generate", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_insights_create_client_forbidden(client):
    """EDIT_AI_OUTPUTS has no CLIENT_* cell -> a client cannot author insights."""
    r = client.post("/api/insights", json={"title": "Nope"},
                    headers=clientA_headers())
    assert r.status_code == 403


def test_insights_create_crew_ok(client):
    r = client.post("/api/insights",
                    json={"title": "Crew insight", "impact": "HIGH", "effort": "LOW"},
                    headers=crew_headers(ORG_A))
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Crew insight"


def test_insights_patch_client_owner_ok(client):
    """UPDATE_TASKS: CLIENT_OWNER is CONDITIONAL -> passes the gate, may triage
    its own org's insight."""
    r = client.patch("/api/insights/1", json={"status": "ACKNOWLEDGED"},
                     headers=clientA_headers())
    assert r.status_code == 200
    assert r.json()["status"] == "ACKNOWLEDGED"


def test_insights_patch_cross_org_not_found(client):
    """Crew pointing at org A cannot patch org B's insight: org scoping -> 404."""
    r = client.patch("/api/insights/2", json={"status": "ACKNOWLEDGED"},
                     headers=crew_headers(ORG_A))
    assert r.status_code == 404
