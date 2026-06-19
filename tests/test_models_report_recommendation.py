"""Data-layer tests for the standalone Report and Recommendation models (§6).

Uses an in-memory SQLite DB and Base.metadata.create_all — no FastAPI needed.
Importing the model modules registers their tables on Base.metadata.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
# Import models so their tables register on Base.metadata before create_all.
# app.models.models brings in the FK targets (organizations, workspaces, users,
# roadmap_items) so create_all can resolve the foreign keys.
import app.models.models  # noqa: F401
from app.models.report import Report, ReportStatus
from app.models.recommendation import Recommendation, RecVisibility


def _session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_report_defaults_and_read():
    db = _session()
    rpt = Report(organization_id=1, title="Q3 Diagnosis")
    db.add(rpt)
    db.commit()
    db.refresh(rpt)

    assert rpt.id is not None
    # status defaults to DRAFT_INTERNAL
    assert rpt.status == ReportStatus.DRAFT_INTERNAL
    assert rpt.status.value == "DRAFT_INTERNAL"
    # visibility string default
    assert rpt.visibility == "DRAFT_INTERNAL"
    # nullable fields stay None
    assert rpt.workspace_id is None
    assert rpt.content is None
    assert rpt.shared_at is None
    # timestamps populated by server_default
    assert rpt.created_at is not None
    assert rpt.updated_at is not None

    # round-trip read
    fetched = db.query(Report).filter_by(id=rpt.id).one()
    assert fetched.title == "Q3 Diagnosis"
    db.close()


def test_report_explicit_status():
    db = _session()
    rpt = Report(
        organization_id=1,
        title="Shared deck",
        status=ReportStatus.CLIENT_SHARED,
        visibility="CLIENT_SHARED",
        content={"sections": [1, 2, 3]},
    )
    db.add(rpt)
    db.commit()
    db.refresh(rpt)

    assert rpt.status == ReportStatus.CLIENT_SHARED
    assert rpt.content == {"sections": [1, 2, 3]}
    db.close()


def test_recommendation_defaults_and_read():
    db = _session()
    rec = Recommendation(
        workspace_id=1,
        organization_id=1,
        text="Automate the monthly close.",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    assert rec.id is not None
    # visibility defaults to INTERNAL
    assert rec.visibility == RecVisibility.INTERNAL
    assert rec.visibility.value == "INTERNAL"
    # nullable fields stay None
    assert rec.dimension is None
    assert rec.impact is None
    assert rec.effort is None
    assert rec.linked_roadmap_item_id is None
    assert rec.created_at is not None
    assert rec.updated_at is not None

    fetched = db.query(Recommendation).filter_by(id=rec.id).one()
    assert fetched.text == "Automate the monthly close."
    db.close()


def test_recommendation_explicit_visibility():
    db = _session()
    rec = Recommendation(
        workspace_id=2,
        organization_id=1,
        dimension="Finanzas",
        text="Restrict to the board.",
        visibility=RecVisibility.EXECUTIVE_ONLY,
        impact="HIGH",
        effort="LOW",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    assert rec.visibility == RecVisibility.EXECUTIVE_ONLY
    assert rec.visibility.value == "EXECUTIVE_ONLY"
    assert rec.impact == "HIGH"
    db.close()
