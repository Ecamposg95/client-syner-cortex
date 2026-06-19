"""Data-layer tests for the §6 collaboration models: WorkspaceUser membership
and the polymorphic Comment.

Runs entirely against an isolated in-memory SQLite database. We register the
core models (which own the FK targets: users, organizations, workspaces) plus
the two new modules, create the schema, then exercise:

  - inserting a workspace membership row,
  - the (workspace_id, user_id) uniqueness guard,
  - inserting a comment over a fictitious object and reading it back by the
    (object_type, object_id) discriminator pair.

Run:
    .venv/bin/python -m pytest tests/test_models_workspace_user_comment.py -q
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base

# Register the models that own the FK targets (users, organizations, workspaces)
# so create_all can resolve foreign keys, plus the two models under test.
from app.models import models as m  # noqa: F401
from app.models.workspace_user import WorkspaceUser
from app.models.comment import Comment


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # SQLite ignores FK ondelete unless PRAGMA is on, but we do not test cascade
    # here; create_all is all we need for the constraints under test.
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_insert_workspace_membership(session):
    member = WorkspaceUser(
        workspace_id=1,
        user_id=42,
        workspace_role="OWNER",
        visibility_scope="ALL",
    )
    session.add(member)
    session.commit()

    rows = session.query(WorkspaceUser).all()
    assert len(rows) == 1
    assert rows[0].workspace_role == "OWNER"
    assert rows[0].visibility_scope == "ALL"
    assert rows[0].id is not None


def test_workspace_user_unique_constraint(session):
    session.add(WorkspaceUser(workspace_id=1, user_id=42, workspace_role="OWNER"))
    session.commit()

    # Same (workspace_id, user_id) pair must be rejected by the unique constraint.
    session.add(WorkspaceUser(workspace_id=1, user_id=42, workspace_role="MEMBER"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # A different workspace for the same user is fine.
    session.add(WorkspaceUser(workspace_id=2, user_id=42, workspace_role="MEMBER"))
    session.commit()
    assert session.query(WorkspaceUser).count() == 2


def test_insert_and_read_comment_by_object(session):
    comment = Comment(
        object_type="REPORT",
        object_id=1,
        organization_id=7,
        author_id=42,
        content="Looks good to me.",
    )
    session.add(comment)
    # A comment on a different object type / id, to prove the lookup filters.
    session.add(
        Comment(
            object_type="TOOLRUN",
            object_id=99,
            organization_id=7,
            author_id=42,
            content="unrelated",
        )
    )
    session.commit()

    found = (
        session.query(Comment)
        .filter(Comment.object_type == "REPORT", Comment.object_id == 1)
        .all()
    )
    assert len(found) == 1
    assert found[0].content == "Looks good to me."
    assert found[0].organization_id == 7
    assert found[0].id is not None
