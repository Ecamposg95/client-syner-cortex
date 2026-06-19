"""Endpoint-level LEAK tests encoding the golden invariant of Task Pack §4.

INVARIANT: a CLIENT_USER of an org must NEVER be able to see, through any HTTP
endpoint, (a) data of ANOTHER organization, nor (b) objects of its own org in an
internal state (INTERNAL_ONLY, DRAFT_*, AI_GENERATED, CONSULTANT_REVIEW, ...).
Syner crew (SYNER_CREW) does see everything within its scope.

These tests hit REAL endpoints through FastAPI's TestClient, not the policy
engine directly. They run against an isolated in-memory SQLite DB so the dev
database is never touched.

Suite-green rule: where an endpoint TODAY filters only by org but NOT by
visibility (a real leak), the test that reveals the leak is marked
``xfail(strict=False)`` so the deuda is documented while the suite stays green.
Tests that already pass (correct behavior) are left as normal asserts.

Run:
    .venv/bin/python -m pytest tests/test_policy_leak_endpoints.py -q
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.security.auth import create_access_token

# Import every model module so all tables are registered on Base.metadata before
# create_all (otherwise the FK tables for clevel/insight/raci/kpi are missing).
from app.models import models as m  # noqa: F401
from app.models import clevel as cl  # noqa: F401
from app.models import insight as ins  # noqa: F401
from app.models import raci as rc  # noqa: F401
from app.models import kpi as kp  # noqa: F401
from app.models import toolkit as tk  # noqa: F401

from app.models.models import (
    User, Organization, OrganizationUser, Workspace, Document,
    Diagnosis, Roadmap, RoadmapItem,
)
from app.models.clevel import (
    ConsultingEngagement, Finding, Decision, Risk,
    EngagementStatus, FindingCriticality, DecisionStatus, RiskStatus,
)
from app.models.insight import (
    Insight, InsightImpact, InsightEffort, InsightStatus, InsightSource,
)
from app.models.raci import RaciMatrix
from app.models.kpi import KPI


# --------------------------------------------------------------------------- #
# Isolated DB + dependency override
# --------------------------------------------------------------------------- #

# Org ids
ORG_A = 100   # client org A
ORG_B = 200   # client org B
ORG_SYNER = 1  # the Syner internal org

# User ids
UID_CREW = 10
UID_A_OWNER = 11
UID_B_OWNER = 12


@pytest.fixture(scope="module")
def db_session():
    """A single in-memory SQLite session shared by the seeded data and the app
    (StaticPool keeps it as one connection across threads)."""
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
            pass  # the module-scoped session is closed by db_session fixture

    app.dependency_overrides[get_db] = _override_get_db
    # The kpi router defines its OWN get_db (it binds SessionLocal directly rather
    # than importing app.database.get_db), so it must be overridden separately or
    # it would hit the real dev DB. Override it by its actual callable identity.
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

    # --- Workspace in org A (and a workspace in org B for cross-org probing) ---
    s.add(Workspace(id=1000, organization_id=ORG_A, name="WS A"))
    s.add(Workspace(id=2000, organization_id=ORG_B, name="WS B"))

    # --- Documents in org A: one shared, one internal ---
    s.add_all([
        Document(id=1, workspace_id=1000, organization_id=ORG_A, name="shared-A",
                 file_type="txt", file_path="/a", visibility="CLIENT_SHARED"),
        Document(id=2, workspace_id=1000, organization_id=ORG_A, name="internal-A",
                 file_type="txt", file_path="/b", visibility="INTERNAL_ONLY"),
    ])
    # A document in org B (to ensure cross-org never bleeds in)
    s.add(Document(id=3, workspace_id=2000, organization_id=ORG_B, name="shared-B",
                   file_type="txt", file_path="/c", visibility="CLIENT_SHARED"))

    # --- Diagnosis in org A: internal + client-visible ---
    s.add_all([
        Diagnosis(id=1, workspace_id=1000, organization_id=ORG_A, user_id=UID_CREW,
                  status="COMPLETED", visibility="CLIENT_VISIBLE"),
        Diagnosis(id=2, workspace_id=1000, organization_id=ORG_A, user_id=UID_CREW,
                  status="COMPLETED", visibility="INTERNAL_ONLY"),
    ])

    # --- Roadmap in org A: an older client-visible one, then a NEWER (latest)
    # INTERNAL_ONLY one. get_latest_roadmap orders by created_at desc with no
    # visibility filter, so a client would receive the internal latest roadmap.
    # The internal roadmap also carries an INTERNAL_ONLY item to test item leak.
    import datetime as _dt
    s.add(Roadmap(id=1, workspace_id=1000, organization_id=ORG_A, diagnosis_id=1,
                  visibility="CLIENT_VISIBLE",
                  created_at=_dt.datetime(2024, 1, 1)))
    s.add(RoadmapItem(id=1, roadmap_id=1, title="client item", dimension="Ops",
                      phase=30, status="DONE", visibility="CLIENT_VISIBLE"))
    # The latest roadmap (newest created_at) is INTERNAL_ONLY.
    s.add(Roadmap(id=2, workspace_id=1000, organization_id=ORG_A, diagnosis_id=1,
                  visibility="INTERNAL_ONLY",
                  created_at=_dt.datetime(2024, 6, 1)))
    s.add(RoadmapItem(id=2, roadmap_id=2, title="internal item", dimension="Ops",
                      phase=30, status="TODO", visibility="INTERNAL_ONLY"))

    # --- C-Level engagement + findings/decisions/risks in org A and B ---
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

    # --- Insights in org A and B ---
    s.add(Insight(id=1, organization_id=ORG_A, title="Insight A",
                  impact=InsightImpact.HIGH, effort=InsightEffort.LOW,
                  priority_score=9.0, quadrant="QUICK_WIN", status=InsightStatus.NEW,
                  is_critical_alarm=False, source_type=InsightSource.MANUAL))
    s.add(Insight(id=2, organization_id=ORG_B, title="Insight B",
                  impact=InsightImpact.HIGH, effort=InsightEffort.LOW,
                  priority_score=9.0, quadrant="QUICK_WIN", status=InsightStatus.NEW,
                  is_critical_alarm=False, source_type=InsightSource.MANUAL))

    # --- RACI matrices in org A and B ---
    s.add(RaciMatrix(id=1, organization_id=ORG_A, name="RACI A", version="1.0"))
    s.add(RaciMatrix(id=2, organization_id=ORG_B, name="RACI B", version="1.0"))

    # --- KPIs in org A and B ---
    s.add(KPI(id=1, organization_id=ORG_A, name="kpi-A", value=1.0))
    s.add(KPI(id=2, organization_id=ORG_B, name="kpi-B", value=2.0))

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
# /api/portal/summary
# =========================================================================== #

def test_portal_summary_client_no_internal_documents(client):
    """Client portal summary must not count INTERNAL_ONLY documents (it filters
    visibility for clients in build_summary)."""
    r = client.get("/api/portal/summary", headers=clientA_headers())
    assert r.status_code == 200
    body = r.json()
    # Only the single CLIENT_SHARED doc should be counted for the client.
    assert body["deliverables"]["document_total"] == 1


def test_portal_summary_client_no_internal_diagnosis(client):
    """Client must only see the CLIENT_VISIBLE diagnosis, never INTERNAL_ONLY."""
    r = client.get("/api/portal/summary", headers=clientA_headers())
    assert r.status_code == 200
    diag = r.json()["diagnosis"]
    assert diag is not None
    assert diag["diagnosis_id"] == 1  # the CLIENT_VISIBLE one, not id=2 internal


def test_portal_summary_crew_sees_all_documents(client):
    """Crew in scope sees every document of the org (no visibility narrowing)."""
    r = client.get("/api/portal/summary", headers=crew_headers(ORG_A))
    assert r.status_code == 200
    assert r.json()["deliverables"]["document_total"] == 2


def test_portal_summary_cross_org_forbidden(client):
    """Client A pointing X-Organization-ID at B must be rejected (membership)."""
    r = client.get("/api/portal/summary", headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


# =========================================================================== #
# /api/documents  (GET "" with workspace_id)
# =========================================================================== #

def test_documents_list_client_hides_internal(client):
    """FIXED (PR2 wiring): the documents listing now goes through scoped_query,
    so a CLIENT_USER no longer sees the INTERNAL_ONLY document of its own org."""
    r = client.get("/api/documents", params={"workspace_id": 1000},
                   headers=clientA_headers())
    assert r.status_code == 200
    visibilities = {d["name"] for d in r.json()}
    # Expect ONLY the shared doc; internal-A must be absent.
    assert "internal-A" not in visibilities


def test_documents_list_cross_org_not_found(client):
    """Client A asking for org B's workspace must not get B's documents."""
    # Workspace 2000 belongs to org B; clientA cannot even enter org B.
    r = client.get("/api/documents", params={"workspace_id": 2000},
                   headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


def test_documents_list_crew_sees_internal(client):
    """Crew sees both the shared and the internal document of org A."""
    r = client.get("/api/documents", params={"workspace_id": 1000},
                   headers=crew_headers(ORG_A))
    assert r.status_code == 200
    names = {d["name"] for d in r.json()}
    assert names == {"shared-A", "internal-A"}


# =========================================================================== #
# /api/roadmaps/latest  (workspace-scoped)
# =========================================================================== #

def test_roadmaps_latest_client_hides_internal(client):
    """FIXED (PR2 wiring): the latest roadmap in this seed is INTERNAL_ONLY, so a
    CLIENT_USER must NOT receive it — get_latest_roadmap now 404s rather than
    leaking the internal container and its INTERNAL_ONLY items."""
    r = client.get("/api/roadmaps/latest", params={"workspace_id": 1000},
                   headers=clientA_headers())
    assert r.status_code == 404


def test_roadmaps_latest_cross_org_not_found(client):
    """Client A cannot read org B's workspace roadmap."""
    r = client.get("/api/roadmaps/latest", params={"workspace_id": 2000},
                   headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


# =========================================================================== #
# /api/insights
# =========================================================================== #

def test_insights_cross_org_forbidden(client):
    """Client A with X-Organization-ID=B must be blocked (not get B's insights)."""
    r = client.get("/api/insights", headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


def test_insights_own_org_only(client):
    """Client A sees only org-A insights, never org-B ones."""
    r = client.get("/api/insights", headers=clientA_headers())
    assert r.status_code == 200
    titles = {i["title"] for i in r.json()}
    assert titles == {"Insight A"}
    assert "Insight B" not in titles


# =========================================================================== #
# /api/raci/matrices
# =========================================================================== #

def test_raci_cross_org_forbidden(client):
    r = client.get("/api/raci/matrices", headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


def test_raci_own_org_only(client):
    r = client.get("/api/raci/matrices", headers=clientA_headers())
    assert r.status_code == 200
    names = {x["name"] for x in r.json()}
    assert names == {"RACI A"}


# =========================================================================== #
# /api/kpi
# =========================================================================== #

def test_kpi_cross_org_forbidden(client):
    r = client.get("/api/kpi", headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


def test_kpi_own_org_only(client):
    r = client.get("/api/kpi", headers=clientA_headers())
    assert r.status_code == 200
    names = {k["name"] for k in r.json()}
    assert names == {"kpi-A"}


# =========================================================================== #
# /api/clevel/*  (decisions / risks / engagements / findings)
# =========================================================================== #

def test_clevel_decisions_cross_org_forbidden(client):
    r = client.get("/api/clevel/decisions", headers=clientA_headers(ORG_B))
    assert r.status_code in (403, 404)


def test_clevel_decisions_own_org_only(client):
    r = client.get("/api/clevel/decisions", headers=clientA_headers())
    assert r.status_code == 200
    titles = {d["title"] for d in r.json()}
    assert titles == {"Decision A"}


def test_clevel_risks_own_org_only(client):
    r = client.get("/api/clevel/risks", headers=clientA_headers())
    assert r.status_code == 200
    descs = {x["description"] for x in r.json()}
    assert descs == {"Risk A"}


def test_clevel_engagements_own_org_only(client):
    r = client.get("/api/clevel/engagements", headers=clientA_headers())
    assert r.status_code == 200
    titles = {e["title"] for e in r.json()}
    assert titles == {"Eng A"}


def test_clevel_findings_cross_org_engagement_not_found(client):
    """Client A may not read findings of org B's engagement (id=2): the
    engagement-ownership check must 404/403, never expose B's findings."""
    r = client.get("/api/clevel/engagements/2/findings", headers=clientA_headers())
    assert r.status_code in (403, 404)
    if r.status_code == 200:  # defensive: if it ever 200s, it must be empty
        assert r.json() == []


def test_clevel_findings_own_engagement_ok(client):
    r = client.get("/api/clevel/engagements/1/findings", headers=clientA_headers())
    assert r.status_code == 200
    titles = {f["title"] for f in r.json()}
    assert titles == {"Finding A"}
