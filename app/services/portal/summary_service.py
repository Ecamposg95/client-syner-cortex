"""Aggregates the real consultancy status for a client portal dashboard.

Pulls from existing models (engagement, diagnosis, roadmap, deliverables,
findings, decisions, KPIs) scoped to one organization. Visibility is filtered
for client users so they never see INTERNAL_ONLY / DRAFT_INTERNAL artifacts.
"""
from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    User, Diagnosis, DiagnosisDimension, Roadmap, RoadmapItem, Document,
)
from app.models.clevel import (
    ConsultingEngagement, Finding, Deliverable, Decision,
    EngagementStatus, FindingCriticality, DecisionStatus,
)
from app.models.kpi import KPI

CLIENT_VISIBLE = {"CLIENT_SHARED", "CLIENT_UPLOAD", "APPROVED", "CLIENT_VISIBLE"}


def _is_client(user: User) -> bool:
    return not (user.is_superadmin or user.user_type == "SYNER_CREW")


def build_summary(db: Session, org_id: int, user: User) -> dict:
    client = _is_client(user)

    # ── Engagement (prefer ACTIVE, else most recent) ──
    eng_q = db.query(ConsultingEngagement).filter(ConsultingEngagement.organization_id == org_id)
    engagement = (
        eng_q.filter(ConsultingEngagement.status == EngagementStatus.ACTIVE).first()
        or eng_q.order_by(ConsultingEngagement.id.desc()).first()
    )
    engagement_out = None
    if engagement:
        engagement_out = {
            "id": engagement.id,
            "title": engagement.title,
            "objective": engagement.objective,
            "status": engagement.status.value if engagement.status else None,
            "start_date": engagement.start_date,
            "end_date": engagement.end_date,
        }

    # ── Diagnosis health (latest, visibility-filtered for clients) ──
    diag_q = db.query(Diagnosis).filter(Diagnosis.organization_id == org_id)
    if client:
        diag_q = diag_q.filter(Diagnosis.visibility.in_(CLIENT_VISIBLE))
    diagnosis = diag_q.options(joinedload(Diagnosis.dimensions)).order_by(Diagnosis.created_at.desc()).first()
    diag_out = None
    if diagnosis:
        dims = [
            {"name": d.name, "rating": d.rating, "recommendations": d.recommendations}
            for d in diagnosis.dimensions
        ]
        ratings = [d["rating"] for d in dims if d["rating"] is not None]
        diag_out = {
            "diagnosis_id": diagnosis.id,
            "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "dimensions": dims,
            "top_weaknesses": sorted(dims, key=lambda d: d["rating"] or 99)[:3],
        }

    # ── Roadmap progress 30/60/90 (latest, visibility-filtered for clients) ──
    rm_q = db.query(Roadmap).filter(Roadmap.organization_id == org_id)
    if client:
        rm_q = rm_q.filter(Roadmap.visibility.in_(CLIENT_VISIBLE))
    roadmap = rm_q.order_by(Roadmap.created_at.desc()).first()
    roadmap_out = None
    if roadmap:
        items = db.query(RoadmapItem).filter(RoadmapItem.roadmap_id == roadmap.id)
        if client:
            items = items.filter(RoadmapItem.visibility.in_(CLIENT_VISIBLE))
        items = items.all()
        phases = {}
        for phase in (30, 60, 90):
            pit = [i for i in items if i.phase == phase]
            done = sum(1 for i in pit if i.status == "DONE")
            phases[str(phase)] = {
                "total": len(pit),
                "done": done,
                "in_progress": sum(1 for i in pit if i.status == "IN_PROGRESS"),
                "percent": round(done / len(pit) * 100) if pit else 0,
            }
        total = len(items)
        done_all = sum(1 for i in items if i.status == "DONE")
        roadmap_out = {
            "roadmap_id": roadmap.id,
            "overall_percent": round(done_all / total * 100) if total else 0,
            "phases": phases,
        }

    # ── Deliverables (engagement deliverables + vault documents) ──
    deliverables_by_status = {}
    if engagement:
        for d in db.query(Deliverable).filter(Deliverable.engagement_id == engagement.id).all():
            deliverables_by_status[d.status] = deliverables_by_status.get(d.status, 0) + 1
    doc_q = db.query(Document).filter(Document.organization_id == org_id)
    if client:
        doc_q = doc_q.filter(Document.visibility.in_(CLIENT_VISIBLE))
    documents = doc_q.all()
    docs_by_status = {}
    for d in documents:
        docs_by_status[d.status] = docs_by_status.get(d.status, 0) + 1

    # ── Top findings (CRITICAL / HIGH) ──
    findings_out = []
    if engagement:
        crit = db.query(Finding).filter(
            Finding.engagement_id == engagement.id,
            Finding.criticality.in_([FindingCriticality.CRITICAL, FindingCriticality.HIGH]),
        ).all()
        findings_out = [
            {"id": f.id, "title": f.title, "area": f.area,
             "criticality": f.criticality.value if f.criticality else None,
             "recommendation": f.recommendation}
            for f in crit
        ]

    # ── Open decisions (PENDING) ──
    pending = db.query(Decision).filter(
        Decision.organization_id == org_id, Decision.status == DecisionStatus.PENDING
    ).all()
    decisions_out = [
        {"id": d.id, "title": d.title, "context": d.context,
         "syner_recommendation": d.syner_recommendation, "deadline": d.deadline}
        for d in pending
    ]

    # ── KPIs ──
    kpis_out = [
        {"id": k.id, "name": k.name, "value": k.value, "timestamp": k.timestamp}
        for k in db.query(KPI).filter(KPI.organization_id == org_id).all()
    ]

    return {
        "organization_id": org_id,
        "engagement": engagement_out,
        "diagnosis": diag_out,
        "roadmap": roadmap_out,
        "deliverables": {
            "engagement_by_status": deliverables_by_status,
            "documents_by_status": docs_by_status,
            "document_total": len(documents),
        },
        "critical_findings": findings_out,
        "open_decisions": decisions_out,
        "kpis": kpis_out,
    }
