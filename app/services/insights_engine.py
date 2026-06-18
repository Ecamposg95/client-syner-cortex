"""Cortex Insights engine — distills prioritized, actionable insights from the
organization's existing consulting data (findings, risks, diagnosis dimensions).

Each insight is scored on a classic impact/effort matrix so the highest-leverage
recommendations (high impact + low effort = quick wins) bubble to the top. The
generator is idempotent: it dedupes on (source_type, source_ref) so re-running
after new findings are added only inserts what's new.
"""
from sqlalchemy.orm import Session, joinedload

from app.models.models import Diagnosis
from app.models.clevel import ConsultingEngagement, Finding, Risk, FindingCriticality
from app.models.insight import (
    Insight, InsightImpact, InsightEffort, InsightStatus, InsightSource,
)

_IMPACT_WEIGHT = {InsightImpact.LOW: 1, InsightImpact.MEDIUM: 2, InsightImpact.HIGH: 3}
_EFFORT_WEIGHT = {InsightEffort.LOW: 1, InsightEffort.MEDIUM: 2, InsightEffort.HIGH: 3}


def compute_priority(impact: InsightImpact, effort: InsightEffort) -> tuple[float, str]:
    """Returns (priority_score, quadrant). Impact dominates the score; lighter
    effort breaks ties upward, so high-impact/low-effort 'quick wins' rank first."""
    iw = _IMPACT_WEIGHT[impact]
    ew = _EFFORT_WEIGHT[effort]
    score = float(iw * 10 - ew)
    impact_high = impact in (InsightImpact.HIGH, InsightImpact.MEDIUM)
    effort_high = effort in (InsightEffort.HIGH, InsightEffort.MEDIUM)
    if impact_high and not effort_high:
        quadrant = "QUICK_WIN"
    elif impact_high and effort_high:
        quadrant = "MAJOR_PROJECT"
    elif not impact_high and not effort_high:
        quadrant = "INCREMENTAL"
    else:
        quadrant = "LOW_PRIORITY"
    return score, quadrant


_CRITICALITY_TO_IMPACT = {
    FindingCriticality.CRITICAL: InsightImpact.HIGH,
    FindingCriticality.HIGH: InsightImpact.HIGH,
    FindingCriticality.MEDIUM: InsightImpact.MEDIUM,
    FindingCriticality.LOW: InsightImpact.LOW,
}

_LEVEL_TO_IMPACT = {
    "HIGH": InsightImpact.HIGH,
    "MEDIUM": InsightImpact.MEDIUM,
    "LOW": InsightImpact.LOW,
}


def _build(org_id, *, title, description, category, impact, effort,
           recommended_action, source_type, source_ref, is_critical_alarm=False) -> Insight:
    score, quadrant = compute_priority(impact, effort)
    return Insight(
        organization_id=org_id,
        title=title,
        description=description,
        category=category,
        impact=impact,
        effort=effort,
        priority_score=score,
        quadrant=quadrant,
        status=InsightStatus.NEW,
        is_critical_alarm=is_critical_alarm,
        recommended_action=recommended_action,
        source_type=source_type,
        source_ref=source_ref,
    )


def generate_insights(db: Session, org_id: int) -> dict:
    """(Re)generates insights for an organization from its current findings,
    risks and latest diagnosis. Idempotent — existing source-linked insights are
    left untouched. Returns a summary of what was created and what was scanned."""
    # Source-linked insights already on record, to skip on re-run.
    existing = {
        (row.source_type, row.source_ref)
        for row in db.query(Insight.source_type, Insight.source_ref)
        .filter(Insight.organization_id == org_id, Insight.source_ref.isnot(None))
        .all()
    }

    created: list[Insight] = []

    # ── Findings across the org's engagements ──
    findings = (
        db.query(Finding)
        .join(ConsultingEngagement, Finding.engagement_id == ConsultingEngagement.id)
        .filter(ConsultingEngagement.organization_id == org_id)
        .all()
    )
    for f in findings:
        key = (InsightSource.FINDING, f.id)
        if key in existing:
            continue
        impact = _CRITICALITY_TO_IMPACT.get(f.criticality, InsightImpact.MEDIUM)
        created.append(_build(
            org_id,
            title=f.title,
            description=f.description or f.impact,
            category=f.area,
            impact=impact,
            effort=InsightEffort.MEDIUM,
            recommended_action=f.recommendation,
            source_type=InsightSource.FINDING,
            source_ref=f.id,
            is_critical_alarm=(f.criticality == FindingCriticality.CRITICAL),
        ))
        existing.add(key)

    # ── Open risks (probability x impact) ──
    risks = db.query(Risk).filter(Risk.organization_id == org_id).all()
    for r in risks:
        key = (InsightSource.RISK, r.id)
        if key in existing:
            continue
        impact = _LEVEL_TO_IMPACT.get((r.impact or "").upper(), InsightImpact.MEDIUM)
        prob = (r.probability or "").upper()
        created.append(_build(
            org_id,
            title=f"Riesgo: {r.description}",
            description=f"Categoría: {r.category}" if r.category else None,
            category=r.category,
            impact=impact,
            effort=InsightEffort.MEDIUM,
            recommended_action=r.mitigation_plan,
            source_type=InsightSource.RISK,
            source_ref=r.id,
            is_critical_alarm=(prob == "HIGH" and impact == InsightImpact.HIGH),
        ))
        existing.add(key)

    # ── Weak dimensions from the latest diagnosis (rating <= 2 on a 1-5 scale) ──
    diagnosis = (
        db.query(Diagnosis)
        .filter(Diagnosis.organization_id == org_id)
        .options(joinedload(Diagnosis.dimensions))
        .order_by(Diagnosis.created_at.desc())
        .first()
    )
    if diagnosis:
        for d in diagnosis.dimensions:
            if d.rating is None or d.rating > 2:
                continue
            key = (InsightSource.DIAGNOSIS, d.id)
            if key in existing:
                continue
            impact = InsightImpact.HIGH if d.rating <= 1 else InsightImpact.MEDIUM
            created.append(_build(
                org_id,
                title=f"Debilidad en {d.name} (madurez {d.rating}/5)",
                description=d.findings,
                category=d.name,
                impact=impact,
                effort=InsightEffort.HIGH,  # dimensional gaps are usually structural
                recommended_action=d.recommendations,
                source_type=InsightSource.DIAGNOSIS,
                source_ref=d.id,
                is_critical_alarm=(d.rating <= 1),
            ))
            existing.add(key)

    for ins in created:
        db.add(ins)
    db.commit()

    return {
        "created": len(created),
        "scanned": {
            "findings": len(findings),
            "risks": len(risks),
            "diagnosis_dimensions": len(diagnosis.dimensions) if diagnosis else 0,
        },
    }
