"""Integration test for scoped_query — the repository-layer filter (Eje 1 scope
+ Eje 3 visibility). Uses an in-memory SQLite with the real Document model.

Note: membership (does the client belong to org X?) is Eje 1 enforced at the
dependency layer (get_organization_context / require_action), not in
scoped_query — scoped_query trusts the org_id it is handed. These tests cover
the visibility narrowing it is responsible for.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.models import Document
from app.policy.principal import Principal
from app.policy.deps import scoped_query
from app.policy.visibility import ObjectType


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        Document(workspace_id=1, organization_id=10, name="shared", file_type="txt", file_path="/a", visibility="CLIENT_SHARED"),
        Document(workspace_id=1, organization_id=10, name="internal", file_type="txt", file_path="/b", visibility="INTERNAL_ONLY"),
        Document(workspace_id=1, organization_id=10, name="upload", file_type="txt", file_path="/c", visibility="CLIENT_UPLOAD"),
        Document(workspace_id=1, organization_id=20, name="otherorg", file_type="txt", file_path="/d", visibility="CLIENT_SHARED"),
    ])
    session.commit()
    yield session
    session.close()


def _client():
    return Principal(user_id=3, user_type="CLIENT_USER", org_roles={10: "CLIENT_OWNER"})


def _crew():
    return Principal(user_id=1, user_type="SYNER_CREW", org_roles={10: "SYNER_CONSULTANT"})


def test_client_sees_only_shared_in_org(db):
    rows = scoped_query(db, Document, _client(), 10, object_type=ObjectType.DOCUMENT).all()
    # internal hidden; other-org excluded by org filter; upload excluded (no owner column yet).
    assert sorted(r.visibility for r in rows) == ["CLIENT_SHARED"]


def test_crew_sees_all_in_org_not_other_org(db):
    rows = scoped_query(db, Document, _crew(), 10, object_type=ObjectType.DOCUMENT).all()
    assert len(rows) == 3
    assert all(r.organization_id == 10 for r in rows)


def test_without_object_type_no_visibility_narrowing(db):
    # Crew query with no object type returns all org rows (used for internal lists).
    rows = scoped_query(db, Document, _crew(), 10).all()
    assert len(rows) == 3


# --- Enum-visibility column (ToolRun.visibility is a SQLAlchemy Enum) ---------

from app.models.toolkit import ToolRun, ToolRunStatus, Visibility


@pytest.fixture
def db_toolrun():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    # FKs are not enforced in SQLite by default, so we insert runs without
    # parent rows. status/visibility are real Enum columns.
    session.add_all([
        ToolRun(organization_id=10, tool_id=1, created_by=3,
                status=ToolRunStatus.CLIENT_SHARED, visibility=Visibility.CLIENT_SHARED),
        ToolRun(organization_id=10, tool_id=1, created_by=1,
                status=ToolRunStatus.AI_GENERATED, visibility=Visibility.INTERNAL_ONLY),
        ToolRun(organization_id=20, tool_id=1, created_by=3,
                status=ToolRunStatus.CLIENT_SHARED, visibility=Visibility.CLIENT_SHARED),
    ])
    session.commit()
    yield session
    session.close()


def test_client_sees_only_shared_toolrun_in_org_enum_column(db_toolrun):
    rows = scoped_query(
        db_toolrun, ToolRun, _client(), 10, object_type=ObjectType.TOOLRUN
    ).all()
    # INTERNAL_ONLY hidden; other-org excluded by org filter.
    assert len(rows) == 1
    assert rows[0].visibility == Visibility.CLIENT_SHARED
    assert rows[0].organization_id == 10


def test_crew_sees_all_toolruns_in_org_not_other_org_enum_column(db_toolrun):
    rows = scoped_query(
        db_toolrun, ToolRun, _crew(), 10, object_type=ObjectType.TOOLRUN
    ).all()
    assert len(rows) == 2
    assert all(r.organization_id == 10 for r in rows)
    assert {r.visibility for r in rows} == {Visibility.CLIENT_SHARED, Visibility.INTERNAL_ONLY}
