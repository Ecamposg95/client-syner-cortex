"""Endpoint tests for the Comments / collaboration module (Task Pack §6).

Invariants under test:
  * Crew AND client of the SAME org can create and read comments on an object
    (bidirectional collaboration within the org).
  * A user of ANOTHER org never sees those comments (org-scoped list is empty),
    and cannot even point X-Organization-ID at the foreign org (403/404).
  * Deletion is restricted to the author OR crew: the author may delete their
    own comment, another client may not (403), and crew may delete any.

Isolated in-memory SQLite (StaticPool) so the dev DB is never touched — same
pattern as tests/test_policy_leak_endpoints.py.

Run:
    .venv/bin/python -m pytest tests/test_comments.py -q
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
from app.models import comment as cmt  # noqa: F401
from app.models.models import User, Organization, OrganizationUser

# Mount the comments router under /api the way the orchestrator does at runtime
# (app.main here does not include it yet), so these tests exercise the real
# endpoints. app.main registers a greedy SPA catch-all GET ("/{catchall:path}")
# that would shadow our GET /api/comments if our routes came after it, so we
# splice the new routes in BEFORE that catch-all. Guard against double-mount.
from app.routers import comments as comments_router

if not any(getattr(r, "path", "") == "/api/comments" for r in app.router.routes):
    before = len(app.router.routes)
    app.include_router(comments_router.router, prefix="/api")
    new_routes = app.router.routes[before:]
    del app.router.routes[before:]
    # Insert ahead of the SPA catch-all ("/{catchall:path}") so /api GETs match.
    catchall_idx = next(
        (i for i, r in enumerate(app.router.routes)
         if getattr(r, "path", "") == "/{catchall:path}"),
        len(app.router.routes),
    )
    app.router.routes[catchall_idx:catchall_idx] = new_routes


# Org ids
ORG_SYNER = 1
ORG_A = 100
ORG_B = 200

# User ids
UID_CREW = 10
UID_A_OWNER = 11      # client A, author
UID_A_OTHER = 13      # client A, a different member (cannot delete A_OWNER's)
UID_B_OWNER = 12      # client B (other org)

OBJ_TYPE = "RACI"
OBJ_ID = 555


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
        User(id=UID_A_OTHER, email="otherA@a.io", hashed_password="x",
             full_name="Other A", user_type="CLIENT_USER", is_active=True),
        User(id=UID_B_OWNER, email="ownerB@b.io", hashed_password="x",
             full_name="Owner B", user_type="CLIENT_USER", is_active=True),
    ])
    s.add_all([
        OrganizationUser(organization_id=ORG_SYNER, user_id=UID_CREW, role="SYNER_PARTNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_OWNER, role="CLIENT_OWNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_OTHER, role="CLIENT_USER"),
        OrganizationUser(organization_id=ORG_B, user_id=UID_B_OWNER, role="CLIENT_OWNER"),
    ])
    s.commit()


def _headers(user_id: int, org_id: int) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org_id)}


def _create(client, headers, content) -> dict:
    r = client.post(
        "/api/comments",
        headers=headers,
        json={"object_type": OBJ_TYPE, "object_id": OBJ_ID, "content": content},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _list(client, headers, org_id=ORG_A):
    return client.get(
        "/api/comments",
        headers=headers,
        params={"object_type": OBJ_TYPE, "object_id": OBJ_ID},
    )


# --------------------------------------------------------------------------- #
# Bidirectional collaboration within the same org
# --------------------------------------------------------------------------- #
def test_crew_and_client_same_org_create_and_see(client):
    crew = _headers(UID_CREW, ORG_A)
    a_owner = _headers(UID_A_OWNER, ORG_A)

    c1 = _create(client, a_owner, "client comment")
    c2 = _create(client, crew, "crew comment")

    # author enrichment is present
    assert c1["author_email"] == "ownerA@a.io"
    assert c1["author_name"] == "Owner A"
    assert c1["author_id"] == UID_A_OWNER
    assert c1["organization_id"] == ORG_A

    # Both members of org A see BOTH comments, ordered by created_at.
    for h in (crew, a_owner):
        r = _list(client, h)
        assert r.status_code == 200
        contents = [x["content"] for x in r.json()]
        assert "client comment" in contents
        assert "crew comment" in contents

    # store ids for later tests on the module-scoped state
    test_crew_and_client_same_org_create_and_see.c1 = c1
    test_crew_and_client_same_org_create_and_see.c2 = c2


# --------------------------------------------------------------------------- #
# Cross-org isolation (Eje 1)
# --------------------------------------------------------------------------- #
def test_other_org_does_not_see_comments(client):
    """Client B, in its OWN org, sees none of org A's comments on the object."""
    r = _list(client, _headers(UID_B_OWNER, ORG_B), org_id=ORG_B)
    assert r.status_code == 200
    assert r.json() == []


def test_cross_org_header_forbidden(client):
    """Client B pointing X-Organization-ID at org A is rejected (membership)."""
    r = _list(client, _headers(UID_B_OWNER, ORG_A))
    assert r.status_code in (403, 404)


def test_cross_org_create_forbidden(client):
    """Client B cannot create a comment inside org A."""
    r = client.post(
        "/api/comments",
        headers=_headers(UID_B_OWNER, ORG_A),
        json={"object_type": OBJ_TYPE, "object_id": OBJ_ID, "content": "intruder"},
    )
    assert r.status_code in (403, 404)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def test_list_requires_object_params(client):
    r = client.get("/api/comments", headers=_headers(UID_A_OWNER, ORG_A))
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# Deletion: author or crew only
# --------------------------------------------------------------------------- #
def test_non_author_client_cannot_delete(client):
    """A different client of the SAME org cannot delete someone else's comment."""
    c1 = _create(client, _headers(UID_A_OWNER, ORG_A), "to-delete-by-author")
    r = client.delete(f"/api/comments/{c1['id']}", headers=_headers(UID_A_OTHER, ORG_A))
    assert r.status_code == 403
    # still there
    assert any(x["id"] == c1["id"] for x in _list(client, _headers(UID_A_OWNER, ORG_A)).json())


def test_author_can_delete_own(client):
    c1 = _create(client, _headers(UID_A_OWNER, ORG_A), "mine-to-remove")
    r = client.delete(f"/api/comments/{c1['id']}", headers=_headers(UID_A_OWNER, ORG_A))
    assert r.status_code == 200
    assert not any(x["id"] == c1["id"] for x in _list(client, _headers(UID_A_OWNER, ORG_A)).json())


def test_crew_can_delete_any(client):
    """Crew may delete a client-authored comment in the org."""
    c1 = _create(client, _headers(UID_A_OWNER, ORG_A), "crew-will-remove")
    r = client.delete(f"/api/comments/{c1['id']}", headers=_headers(UID_CREW, ORG_A))
    assert r.status_code == 200
    assert not any(x["id"] == c1["id"] for x in _list(client, _headers(UID_CREW, ORG_A)).json())


def test_delete_cross_org_not_found(client):
    """Deleting a foreign-org comment from the wrong org context yields 404, not 403."""
    c1 = _create(client, _headers(UID_A_OWNER, ORG_A), "org-a-only")
    r = client.delete(f"/api/comments/{c1['id']}", headers=_headers(UID_B_OWNER, ORG_B))
    assert r.status_code == 404
