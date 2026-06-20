"""Endpoint tests for the Recommendations module (§6), following the isolated
in-memory SQLite pattern of tests/test_policy_leak_endpoints.py.

Golden invariants exercised here:
  - Crew can create, list, edit and SHARE recommendations.
  - A CLIENT_USER sees SHARED and TASK_VISIBLE recommendations of its org, but
    NEVER INTERNAL ones.
  - EXECUTIVE_ONLY is visible only to the client OWNER/EXECUTIVE tier.
  - Cross-org access never leaks (404/403).
  - A client cannot create a recommendation (403, EDIT_AI_OUTPUTS is crew-only).

Run:
    .venv/bin/python -m pytest tests/test_recommendations.py -q
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
from app.models import recommendation as rec_mod  # noqa: F401

from app.models.models import (
    User, Organization, OrganizationUser, Workspace,
    Diagnosis, Roadmap,
)
from app.models.recommendation import Recommendation, RecVisibility


# --------------------------------------------------------------------------- #
# Ids
# --------------------------------------------------------------------------- #
ORG_A = 100
ORG_B = 200
ORG_SYNER = 1

UID_CREW = 10
UID_A_OWNER = 11        # CLIENT_OWNER of org A (executive tier)
UID_A_VIEWER = 13       # CLIENT_VIEWER of org A (non-executive tier)
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
    from app.routers import kpi as kpi_router
    app.dependency_overrides[kpi_router.get_db] = _override_get_db

    # The recommendations router is mounted by the orchestrator under /api in
    # production (alongside the other routers, BEFORE the SPA catch-all that
    # main.py registers last). main.py is out of scope for this module, so we
    # mount the router here. Because main.py already owns a GET "/{catchall:path}"
    # SPA fallback that would shadow our GET routes if we merely appended, we
    # insert the new routes at the FRONT of the app's route table — reproducing
    # the production ordering where API routers precede the catch-all.
    from app.routers import recommendations as rec_router
    already = any(
        getattr(r, "path", "").startswith("/api/recommendations")
        for r in app.routes
    )
    if not already:
        before = len(app.router.routes)
        app.include_router(rec_router.router, prefix="/api")
        new_routes = app.router.routes[before:]
        del app.router.routes[before:]
        app.router.routes[:0] = new_routes

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
        User(id=UID_A_VIEWER, email="viewerA@a.io", hashed_password="x",
             full_name="Viewer A", user_type="CLIENT_USER", is_active=True),
        User(id=UID_B_OWNER, email="ownerB@b.io", hashed_password="x",
             full_name="Owner B", user_type="CLIENT_USER", is_active=True),
    ])
    s.add_all([
        OrganizationUser(organization_id=ORG_SYNER, user_id=UID_CREW, role="SYNER_PARTNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_OWNER, role="CLIENT_OWNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_VIEWER, role="CLIENT_VIEWER"),
        OrganizationUser(organization_id=ORG_B, user_id=UID_B_OWNER, role="CLIENT_OWNER"),
    ])
    s.add(Workspace(id=WS_A, organization_id=ORG_A, name="WS A"))
    s.add(Workspace(id=WS_B, organization_id=ORG_B, name="WS B"))

    # Recommendations in org A: one per visibility.
    s.add_all([
        Recommendation(id=1, workspace_id=WS_A, organization_id=ORG_A,
                       dimension="Ventas", text="rec shared A",
                       visibility=RecVisibility.SHARED, impact="HIGH", effort="LOW"),
        Recommendation(id=2, workspace_id=WS_A, organization_id=ORG_A,
                       dimension="Operaciones", text="rec internal A",
                       visibility=RecVisibility.INTERNAL, impact="HIGH", effort="HIGH"),
        Recommendation(id=3, workspace_id=WS_A, organization_id=ORG_A,
                       dimension="Ventas", text="rec exec-only A",
                       visibility=RecVisibility.EXECUTIVE_ONLY, impact="HIGH", effort="LOW"),
        Recommendation(id=4, workspace_id=WS_A, organization_id=ORG_A,
                       dimension="RH", text="rec task-visible A",
                       visibility=RecVisibility.TASK_VISIBLE, impact="LOW", effort="LOW"),
    ])
    # A recommendation in org B (cross-org probe).
    s.add(Recommendation(id=5, workspace_id=WS_B, organization_id=ORG_B,
                         dimension="Ventas", text="rec shared B",
                         visibility=RecVisibility.SHARED, impact="HIGH", effort="LOW"))

    # A diagnosis + roadmap container in org A so convert-to-roadmap works.
    s.add(Diagnosis(id=1, workspace_id=WS_A, organization_id=ORG_A, user_id=UID_CREW,
                    status="COMPLETED", visibility="CLIENT_VISIBLE"))
    import datetime as _dt
    s.add(Roadmap(id=1, workspace_id=WS_A, organization_id=ORG_A, diagnosis_id=1,
                  visibility="CLIENT_VISIBLE", created_at=_dt.datetime(2024, 1, 1)))

    s.commit()


# --------------------------------------------------------------------------- #
# Auth helpers
# --------------------------------------------------------------------------- #
def _headers(user_id: int, org_id: int) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org_id)}


def crew_headers(org_id: int = ORG_A) -> dict:
    return _headers(UID_CREW, org_id)


def ownerA_headers(org_id: int = ORG_A) -> dict:
    return _headers(UID_A_OWNER, org_id)


def viewerA_headers(org_id: int = ORG_A) -> dict:
    return _headers(UID_A_VIEWER, org_id)


# =========================================================================== #
# Listing / visibility
# =========================================================================== #
def test_crew_sees_all_recommendations(client):
    r = client.get("/api/recommendations", headers=crew_headers())
    assert r.status_code == 200
    texts = {x["text"] for x in r.json()}
    assert texts == {"rec shared A", "rec internal A", "rec exec-only A", "rec task-visible A"}


def test_client_viewer_sees_shared_and_task_visible_not_internal(client):
    """A non-executive client sees SHARED + TASK_VISIBLE, never INTERNAL,
    and not EXECUTIVE_ONLY."""
    r = client.get("/api/recommendations", headers=viewerA_headers())
    assert r.status_code == 200
    texts = {x["text"] for x in r.json()}
    assert "rec shared A" in texts
    assert "rec task-visible A" in texts
    assert "rec internal A" not in texts
    assert "rec exec-only A" not in texts


def test_client_executive_sees_executive_only(client):
    """OWNER/EXECUTIVE tier additionally sees EXECUTIVE_ONLY (still not INTERNAL)."""
    r = client.get("/api/recommendations", headers=ownerA_headers())
    assert r.status_code == 200
    texts = {x["text"] for x in r.json()}
    assert "rec exec-only A" in texts
    assert "rec shared A" in texts
    assert "rec task-visible A" in texts
    assert "rec internal A" not in texts


def test_list_dimension_filter(client):
    r = client.get("/api/recommendations", params={"dimension": "Ventas"},
                   headers=crew_headers())
    assert r.status_code == 200
    assert {x["dimension"] for x in r.json()} == {"Ventas"}


def test_cross_org_list_forbidden(client):
    """Client A pointing at org B is rejected by membership validation."""
    r = client.get("/api/recommendations", headers=ownerA_headers(ORG_B))
    assert r.status_code in (403, 404)


# =========================================================================== #
# Detail
# =========================================================================== #
def test_client_detail_internal_404(client):
    """The INTERNAL recommendation must 404 for a client (existence hidden)."""
    r = client.get("/api/recommendations/2", headers=ownerA_headers())
    assert r.status_code == 404


def test_client_detail_shared_ok(client):
    r = client.get("/api/recommendations/1", headers=ownerA_headers())
    assert r.status_code == 200
    assert r.json()["text"] == "rec shared A"


def test_detail_cross_org_404(client):
    """Crew in org A cannot fetch org B's recommendation by id."""
    r = client.get("/api/recommendations/5", headers=crew_headers(ORG_A))
    assert r.status_code == 404


def test_viewer_executive_only_detail_404(client):
    """Non-executive client 404s on an EXECUTIVE_ONLY recommendation."""
    r = client.get("/api/recommendations/3", headers=viewerA_headers())
    assert r.status_code == 404


# =========================================================================== #
# Create
# =========================================================================== #
def test_crew_can_create(client):
    payload = {
        "workspace_id": WS_A, "organization_id": ORG_A,
        "dimension": "Tecnologia", "text": "nueva rec crew",
        "visibility": "INTERNAL", "impact": "MEDIUM", "effort": "MEDIUM",
    }
    r = client.post("/api/recommendations", json=payload, headers=crew_headers())
    assert r.status_code == 201
    body = r.json()
    assert body["text"] == "nueva rec crew"
    assert body["organization_id"] == ORG_A
    assert body["visibility"] == "INTERNAL"


def test_client_cannot_create_403(client):
    payload = {
        "workspace_id": WS_A, "organization_id": ORG_A,
        "text": "rec del cliente", "visibility": "SHARED",
    }
    r = client.post("/api/recommendations", json=payload, headers=ownerA_headers())
    assert r.status_code == 403


def test_create_workspace_cross_org_404(client):
    """Crew can't seed a recommendation onto another org's workspace."""
    payload = {
        "workspace_id": WS_B, "organization_id": ORG_A,
        "text": "rec mala", "visibility": "INTERNAL",
    }
    r = client.post("/api/recommendations", json=payload, headers=crew_headers(ORG_A))
    assert r.status_code == 404


# =========================================================================== #
# Edit / share
# =========================================================================== #
def test_crew_can_share(client):
    """Sharing = PATCH visibility to SHARED; the client then sees it."""
    r = client.patch("/api/recommendations/2", json={"visibility": "SHARED"},
                     headers=crew_headers())
    assert r.status_code == 200
    assert r.json()["visibility"] == "SHARED"

    # The client (viewer) now sees the previously-internal recommendation.
    r2 = client.get("/api/recommendations/2", headers=viewerA_headers())
    assert r2.status_code == 200
    assert r2.json()["text"] == "rec internal A"


def test_crew_can_edit_fields(client):
    r = client.patch("/api/recommendations/1",
                     json={"impact": "LOW", "effort": "HIGH", "text": "rec shared A v2"},
                     headers=crew_headers())
    assert r.status_code == 200
    body = r.json()
    assert body["impact"] == "LOW"
    assert body["effort"] == "HIGH"
    assert body["text"] == "rec shared A v2"


def test_client_cannot_edit_403(client):
    r = client.patch("/api/recommendations/1", json={"text": "hack"},
                     headers=ownerA_headers())
    assert r.status_code == 403


def test_edit_cross_org_404(client):
    r = client.patch("/api/recommendations/5", json={"impact": "LOW"},
                     headers=crew_headers(ORG_A))
    assert r.status_code == 404


# =========================================================================== #
# Convert to roadmap
# =========================================================================== #
def test_convert_to_roadmap_links_item(client):
    r = client.post("/api/recommendations/4/convert-to-roadmap", headers=crew_headers())
    assert r.status_code == 200
    body = r.json()
    assert body["linked_roadmap_item_id"] is not None

    # Idempotent-ish: calling again returns the same link, no error.
    r2 = client.post("/api/recommendations/4/convert-to-roadmap", headers=crew_headers())
    assert r2.status_code == 200
    assert r2.json()["linked_roadmap_item_id"] == body["linked_roadmap_item_id"]


def test_convert_to_roadmap_client_403(client):
    r = client.post("/api/recommendations/1/convert-to-roadmap", headers=ownerA_headers())
    assert r.status_code == 403
