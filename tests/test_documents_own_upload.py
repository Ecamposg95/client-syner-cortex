"""Eje 3 — own-only CLIENT_UPLOAD visibility for documents.

INVARIANT (Task Pack §4): a CLIENT_USER sees, in the documents listing,
  - its OWN CLIENT_UPLOAD documents (uploaded_by == its user id),
  - the org's CLIENT_SHARED documents (shared with all clients),
but NEVER
  - another client user's CLIENT_UPLOAD (own-only is strictly per-uploader),
  - any INTERNAL_ONLY document.
Syner crew sees everything in scope (no visibility narrowing).

These tests hit the REAL GET /api/documents endpoint through FastAPI's
TestClient against an isolated in-memory SQLite DB (the dev DB is untouched).
The new Document.uploaded_by column is created by Base.metadata.create_all,
so no Alembic migration is needed for the test to run.

Run:
    .venv/bin/python -m pytest tests/test_documents_own_upload.py -q
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.security.auth import create_access_token

# Register every model module so all tables exist on Base.metadata before create_all.
from app.models import models as m  # noqa: F401
from app.models import clevel as cl  # noqa: F401
from app.models import insight as ins  # noqa: F401
from app.models import raci as rc  # noqa: F401
from app.models import kpi as kp  # noqa: F401
from app.models import toolkit as tk  # noqa: F401

from app.models.models import (
    User, Organization, OrganizationUser, Workspace, Document,
)


# Org ids
ORG_A = 100        # client org A
ORG_SYNER = 1      # Syner internal org

# User ids
UID_CREW = 10
UID_A_OWNER = 11   # client user A (the "self")
UID_A_OTHER = 13   # another client user in the SAME org A

# Workspace
WS_A = 1000


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
        User(id=UID_A_OWNER, email="ownerA@a.io", hashed_password="x",
             full_name="Owner A", user_type="CLIENT_USER", is_active=True),
        User(id=UID_A_OTHER, email="otherA@a.io", hashed_password="x",
             full_name="Other A", user_type="CLIENT_USER", is_active=True),
    ])
    s.add_all([
        OrganizationUser(organization_id=ORG_SYNER, user_id=UID_CREW, role="SYNER_PARTNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_OWNER, role="CLIENT_OWNER"),
        OrganizationUser(organization_id=ORG_A, user_id=UID_A_OTHER, role="CLIENT_CONTRIBUTOR"),
    ])
    s.add(Workspace(id=WS_A, organization_id=ORG_A, name="WS A"))

    # Four documents in the same org A workspace:
    s.add_all([
        # Shared with all clients.
        Document(id=1, workspace_id=WS_A, organization_id=ORG_A, name="shared-A",
                 file_type="txt", file_path="/shared", visibility="CLIENT_SHARED"),
        # Internal — no client may see it.
        Document(id=2, workspace_id=WS_A, organization_id=ORG_A, name="internal-A",
                 file_type="txt", file_path="/internal", visibility="INTERNAL_ONLY"),
        # OWNER A's own upload — only OWNER A should see it.
        Document(id=3, workspace_id=WS_A, organization_id=ORG_A, name="my-upload",
                 file_type="txt", file_path="/mine", visibility="CLIENT_UPLOAD",
                 uploaded_by=UID_A_OWNER),
        # OTHER A's own upload — OWNER A must NOT see it (own-only is per-uploader).
        Document(id=4, workspace_id=WS_A, organization_id=ORG_A, name="other-upload",
                 file_type="txt", file_path="/other", visibility="CLIENT_UPLOAD",
                 uploaded_by=UID_A_OTHER),
    ])
    s.commit()


def _headers(user_id: int, org_id: int) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org_id)}


def _list_names(client, user_id: int) -> set[str]:
    r = client.get("/api/documents", params={"workspace_id": WS_A},
                   headers=_headers(user_id, ORG_A))
    assert r.status_code == 200, r.text
    return {d["name"] for d in r.json()}


def test_client_sees_own_upload(client):
    """OWNER A sees its own CLIENT_UPLOAD document."""
    names = _list_names(client, UID_A_OWNER)
    assert "my-upload" in names


def test_client_does_not_see_other_users_upload(client):
    """OWNER A must NOT see another user's CLIENT_UPLOAD in the same org."""
    names = _list_names(client, UID_A_OWNER)
    assert "other-upload" not in names


def test_client_still_sees_shared(client):
    """The shared CLIENT_SHARED document is still visible to the client."""
    names = _list_names(client, UID_A_OWNER)
    assert "shared-A" in names


def test_client_never_sees_internal(client):
    """INTERNAL_ONLY documents are never visible to a client."""
    names = _list_names(client, UID_A_OWNER)
    assert "internal-A" not in names


def test_client_exact_visible_set(client):
    """OWNER A sees exactly {shared, own upload} — nothing else."""
    names = _list_names(client, UID_A_OWNER)
    assert names == {"shared-A", "my-upload"}


def test_crew_sees_everything(client):
    """Crew in scope sees every document, including both clients' uploads."""
    names = _list_names(client, UID_CREW)
    assert names == {"shared-A", "internal-A", "my-upload", "other-upload"}
