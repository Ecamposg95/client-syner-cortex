"""Tests for the superadmin platform-configuration module (`/settings`).

Settings are platform-wide (NOT org-scoped) and editable ONLY by a superadmin.
These tests assert that golden contract on real endpoints:
  * a superadmin can list and upsert settings,
  * a non-superadmin SYNER_CREW gets 403,
  * a CLIENT_USER gets 403,
  * secret-looking values (keys containing KEY/SECRET/TOKEN) are masked in
    responses so credentials never leak.

Runs against an isolated in-memory SQLite DB (pattern from
test_policy_leak_endpoints.py); the dev database is never touched. The router is
mounted on a throwaway FastAPI app under `/api` (mirroring how the orchestrator
wires it) so the test does not depend on app.main including it yet.

Run:
    .venv/bin/python -m pytest tests/test_settings.py -q
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.security.auth import create_access_token

# Register every model on Base.metadata before create_all (users FK target, etc.)
from app.models import models as m  # noqa: F401
from app.models import app_setting as aps  # noqa: F401
from app.models.models import User
from app.models.app_setting import AppSetting
from app.routers import settings as settings_router

# User ids
UID_SUPER = 1
UID_CREW = 2
UID_CLIENT = 3


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

    app = FastAPI()
    app.include_router(settings_router.router, prefix="/api")
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed(s):
    s.add_all([
        User(id=UID_SUPER, email="super@syner.io", hashed_password="x",
             full_name="Super", user_type="SYNER_CREW", is_active=True,
             is_superadmin=True),
        User(id=UID_CREW, email="crew@syner.io", hashed_password="x",
             full_name="Crew", user_type="SYNER_CREW", is_active=True,
             is_superadmin=False),
        User(id=UID_CLIENT, email="client@a.io", hashed_password="x",
             full_name="Client", user_type="CLIENT_USER", is_active=True,
             is_superadmin=False),
    ])
    # A non-secret setting and a secret-looking one (already stored).
    s.add(AppSetting(key="RAG_TOP_K", value="5", category="RAG",
                     description="Fragmentos recuperados"))
    s.add(AppSetting(key="OPENAI_API_KEY", value="sk-supersecret-123",
                     category="INTEGRATIONS", description="Clave API"))
    s.commit()


def _headers(user_id: int) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Authorization: superadmin only
# --------------------------------------------------------------------------- #

def test_superadmin_can_list_settings(client):
    r = client.get("/api/settings", headers=_headers(UID_SUPER))
    assert r.status_code == 200
    keys = {s["key"] for s in r.json()}
    assert "RAG_TOP_K" in keys


def test_non_superadmin_crew_forbidden(client):
    r = client.get("/api/settings", headers=_headers(UID_CREW))
    assert r.status_code == 403


def test_client_user_forbidden(client):
    r = client.get("/api/settings", headers=_headers(UID_CLIENT))
    assert r.status_code == 403


def test_client_user_cannot_upsert(client):
    r = client.put("/api/settings/RAG_TOP_K", json={"key": "RAG_TOP_K", "value": "9"},
                   headers=_headers(UID_CLIENT))
    assert r.status_code == 403


# --------------------------------------------------------------------------- #
# Upsert behaviour
# --------------------------------------------------------------------------- #

def test_superadmin_can_update_existing(client):
    r = client.put(
        "/api/settings/RAG_TOP_K",
        json={"key": "RAG_TOP_K", "value": "8", "category": "RAG"},
        headers=_headers(UID_SUPER),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["value"] == "8"
    assert body["updated_by"] == UID_SUPER


def test_superadmin_can_create_new(client):
    r = client.put(
        "/api/settings/MAX_UPLOAD_MB",
        json={"key": "MAX_UPLOAD_MB", "value": "50", "category": "LIMITS",
              "description": "Tamaño máximo"},
        headers=_headers(UID_SUPER),
    )
    assert r.status_code == 200
    assert r.json()["value"] == "50"
    # And it now appears in the listing.
    r2 = client.get("/api/settings", headers=_headers(UID_SUPER))
    assert "MAX_UPLOAD_MB" in {s["key"] for s in r2.json()}


# --------------------------------------------------------------------------- #
# Secret masking
# --------------------------------------------------------------------------- #

def test_secret_value_masked_in_list(client):
    r = client.get("/api/settings", headers=_headers(UID_SUPER))
    assert r.status_code == 200
    by_key = {s["key"]: s for s in r.json()}
    # The real secret must never be returned in plaintext.
    assert by_key["OPENAI_API_KEY"]["value"] == "****"
    # Non-secret values are returned as-is.
    assert by_key["RAG_TOP_K"]["value"] != "****"


def test_secret_value_masked_on_upsert(client):
    r = client.put(
        "/api/settings/SLACK_TOKEN",
        json={"key": "SLACK_TOKEN", "value": "xoxb-abc-123", "category": "INTEGRATIONS"},
        headers=_headers(UID_SUPER),
    )
    assert r.status_code == 200
    assert r.json()["value"] == "****"


def test_effective_masks_secrets_and_overlays_defaults(client):
    r = client.get("/api/settings/effective", headers=_headers(UID_SUPER))
    assert r.status_code == 200
    settings = r.json()["settings"]
    # A pure default (not stored) shows up with source=default.
    assert settings["AI_PROVIDER"]["source"] == "default"
    # The stored secret is masked here too.
    assert settings["OPENAI_API_KEY"]["value"] == "****"
    # An override reflects the persisted value and source=override.
    assert settings["RAG_TOP_K"]["source"] == "override"


def test_effective_forbidden_for_client(client):
    r = client.get("/api/settings/effective", headers=_headers(UID_CLIENT))
    assert r.status_code == 403
