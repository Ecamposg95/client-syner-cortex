from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import datetime

from app.database import get_db
from app.dependencies import get_current_org_id
from app.policy import Action
from app.policy.deps import require_action
from app.models.insight import (
    Insight, InsightImpact, InsightEffort, InsightStatus, InsightSource,
)
from app.services.insights_engine import generate_insights, compute_priority

router = APIRouter()

# Wiring de política (Fase 3): los guards ad-hoc por lista de strings se
# reemplazan por acciones §8 vía require_action, eliminando cualquier drift de
# nombre de rol. Mapeo aplicado:
#   - POST /insights/generate  -> RUN_TOOLS       (regenera desde fuentes/IA)
#   - POST /insights           -> EDIT_AI_OUTPUTS (autoría de contenido IA)
#   - PATCH /insights/{id}      -> UPDATE_TASKS    (triage del ciclo de vida;
#                                                   clientes con permiso pasan)
# Las acciones de lectura (list/matrix/critical-alarms) siguen org-scoped por
# get_current_org_id; Insight no tiene columna `visibility`, así que no hay
# narrowing de visibilidad por objeto.

# Quadrants ordered from highest to lowest leverage (used to shape the matrix).
_QUADRANTS = ["QUICK_WIN", "MAJOR_PROJECT", "INCREMENTAL", "LOW_PRIORITY"]
_OPEN_STATUSES = [InsightStatus.NEW, InsightStatus.ACKNOWLEDGED, InsightStatus.IN_PROGRESS]


# --- Pydantic Schemas ---

class InsightOut(BaseModel):
    id: int
    title: str
    description: str | None
    category: str | None
    impact: str
    effort: str
    priority_score: float
    quadrant: str | None
    status: str
    is_critical_alarm: bool
    recommended_action: str | None
    source_type: str
    source_ref: int | None
    created_at: datetime.datetime


class InsightCreate(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    impact: str = "MEDIUM"
    effort: str = "MEDIUM"
    recommended_action: str | None = None
    is_critical_alarm: bool = False


class InsightUpdate(BaseModel):
    status: str | None = None
    impact: str | None = None
    effort: str | None = None
    recommended_action: str | None = None


class MatrixCell(BaseModel):
    quadrant: str
    count: int
    items: List[InsightOut]


class InsightMatrix(BaseModel):
    quadrants: List[MatrixCell]
    total: int
    critical_alarms: int


def _serialize(i: Insight) -> dict:
    return {
        "id": i.id,
        "title": i.title,
        "description": i.description,
        "category": i.category,
        "impact": i.impact.value,
        "effort": i.effort.value,
        "priority_score": i.priority_score,
        "quadrant": i.quadrant,
        "status": i.status.value,
        "is_critical_alarm": i.is_critical_alarm,
        "recommended_action": i.recommended_action,
        "source_type": i.source_type.value,
        "source_ref": i.source_ref,
        "created_at": i.created_at,
    }


def _parse_enum(enum_cls, value: str, field: str):
    try:
        return enum_cls(value)
    except ValueError:
        valid = sorted(m.value for m in enum_cls)
        raise HTTPException(status_code=400, detail=f"Invalid {field}. Must be one of {valid}")


# --- Endpoints ---

@router.get("/insights", response_model=List[InsightOut], tags=["insights"])
def list_insights(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    impact: Optional[str] = Query(None),
    quadrant: Optional[str] = Query(None),
    only_alarms: bool = Query(False),
    org_id: int = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    q = db.query(Insight).filter(Insight.organization_id == org_id)
    if status:
        q = q.filter(Insight.status == _parse_enum(InsightStatus, status, "status"))
    if impact:
        q = q.filter(Insight.impact == _parse_enum(InsightImpact, impact, "impact"))
    if category:
        q = q.filter(Insight.category == category)
    if quadrant:
        q = q.filter(Insight.quadrant == quadrant)
    if only_alarms:
        q = q.filter(Insight.is_critical_alarm.is_(True))
    rows = q.order_by(Insight.priority_score.desc(), Insight.id.desc()).all()
    return [_serialize(i) for i in rows]


@router.get("/insights/matrix", response_model=InsightMatrix, tags=["insights"])
def insights_matrix(
    org_id: int = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    """Impact/effort prioritization matrix: open insights grouped by quadrant,
    each ordered by priority. Resolved/dismissed insights are excluded."""
    rows = (
        db.query(Insight)
        .filter(Insight.organization_id == org_id, Insight.status.in_(_OPEN_STATUSES))
        .order_by(Insight.priority_score.desc(), Insight.id.desc())
        .all()
    )
    buckets = {q: [] for q in _QUADRANTS}
    for i in rows:
        buckets.setdefault(i.quadrant or "INCREMENTAL", []).append(_serialize(i))
    cells = [{"quadrant": q, "count": len(buckets[q]), "items": buckets[q]} for q in _QUADRANTS]
    return {
        "quadrants": cells,
        "total": len(rows),
        "critical_alarms": sum(1 for i in rows if i.is_critical_alarm),
    }


@router.get("/insights/critical-alarms", response_model=List[InsightOut], tags=["insights"])
def critical_alarms(
    org_id: int = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Insight)
        .filter(
            Insight.organization_id == org_id,
            Insight.is_critical_alarm.is_(True),
            Insight.status.in_(_OPEN_STATUSES),
        )
        .order_by(Insight.priority_score.desc(), Insight.id.desc())
        .all()
    )
    return [_serialize(i) for i in rows]


@router.post(
    "/insights/generate",
    response_model=dict,
    tags=["insights"],
    # §8 RUN_TOOLS: crew (ADMIN/PARTNER/CONSULTANT ALLOW; ANALYST/PM CONDITIONAL).
    dependencies=[Depends(require_action(Action.RUN_TOOLS))],
)
def run_generation(
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
):
    """Regenerates insights from the org's findings, risks and latest diagnosis.
    Idempotent — only new source-linked insights are added."""
    return generate_insights(db, org_id)


@router.post(
    "/insights",
    response_model=InsightOut,
    tags=["insights"],
    # §8 EDIT_AI_OUTPUTS: autoría/edición de outputs IA por crew.
    dependencies=[Depends(require_action(Action.EDIT_AI_OUTPUTS))],
)
def create_insight(
    payload: InsightCreate,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
):
    impact = _parse_enum(InsightImpact, payload.impact, "impact")
    effort = _parse_enum(InsightEffort, payload.effort, "effort")
    score, quadrant = compute_priority(impact, effort)
    insight = Insight(
        organization_id=org_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        impact=impact,
        effort=effort,
        priority_score=score,
        quadrant=quadrant,
        status=InsightStatus.NEW,
        is_critical_alarm=payload.is_critical_alarm,
        recommended_action=payload.recommended_action,
        source_type=InsightSource.MANUAL,
        source_ref=None,
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return _serialize(insight)


@router.patch(
    "/insights/{insight_id}",
    response_model=InsightOut,
    tags=["insights"],
    # §8 UPDATE_TASKS: crew ALLOW; CLIENT_MANAGER/CONTRIBUTOR ALLOW;
    # CLIENT_OWNER/EXECUTIVE CONDITIONAL (pasan el gate). Triage del ciclo de
    # vida del insight. Insight es org-scoped abajo (404 fuera de org).
    dependencies=[Depends(require_action(Action.UPDATE_TASKS))],
)
def update_insight(
    insight_id: int,
    payload: InsightUpdate,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
):
    insight = db.query(Insight).filter(
        Insight.id == insight_id,
        Insight.organization_id == org_id,
    ).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    if payload.status is not None:
        insight.status = _parse_enum(InsightStatus, payload.status, "status")
    if payload.impact is not None:
        insight.impact = _parse_enum(InsightImpact, payload.impact, "impact")
    if payload.effort is not None:
        insight.effort = _parse_enum(InsightEffort, payload.effort, "effort")
    if payload.recommended_action is not None:
        insight.recommended_action = payload.recommended_action

    # Re-derive score/quadrant whenever impact or effort changed.
    if payload.impact is not None or payload.effort is not None:
        insight.priority_score, insight.quadrant = compute_priority(insight.impact, insight.effort)

    db.commit()
    db.refresh(insight)
    return _serialize(insight)
