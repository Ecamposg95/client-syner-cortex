"""Command Center / Boardroom — cross-org portfolio aggregation for the crew.

A bird's-eye view of EVERY client's health in one place. Strictly crew-only:
gated behind get_current_syner_crew, so a CLIENT_USER can never reach it. Reuses
the counting pattern from app.routers.admin.list_clients (users / workspaces /
enabled modules) and layers on the C-Level + Insights signals (engagements,
findings, insights, pending decisions) that matter for portfolio triage.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_syner_crew
from app.models.models import (
    Organization, OrganizationUser, User, Workspace, OrganizationModule,
)
from app.models.clevel import (
    ConsultingEngagement, Finding, Decision, DecisionStatus,
)
from app.models.insight import Insight

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/summary")
def portfolio_summary(
    db: Session = Depends(get_db),
    _crew: User = Depends(get_current_syner_crew),
):
    """Cross-org portfolio health. Crew sees ALL clients; no org scoping applies.

    Returns ``{ totals: {...}, clients: [ {...} ] }`` where each client card
    carries its user / workspace / module counts plus the C-Level and Insights
    signals used for triage.
    """
    orgs = (
        db.query(Organization)
        .filter(Organization.organization_type == "CLIENT")
        .all()
    )

    clients = []
    total_users = 0
    total_workspaces = 0
    total_modules = 0
    total_engagements = 0
    total_insights = 0
    total_findings = 0
    total_pending_decisions = 0

    for o in orgs:
        users = (
            db.query(OrganizationUser)
            .filter(OrganizationUser.organization_id == o.id)
            .count()
        )
        workspaces = (
            db.query(Workspace)
            .filter(Workspace.organization_id == o.id)
            .count()
        )
        modules = (
            db.query(OrganizationModule)
            .filter(
                OrganizationModule.organization_id == o.id,
                OrganizationModule.is_enabled == True,  # noqa: E712
            )
            .count()
        )
        engagements = (
            db.query(ConsultingEngagement)
            .filter(ConsultingEngagement.organization_id == o.id)
            .count()
        )
        # Findings hang off engagements (no direct org_id), so join through them.
        findings = (
            db.query(Finding)
            .join(
                ConsultingEngagement,
                Finding.engagement_id == ConsultingEngagement.id,
            )
            .filter(ConsultingEngagement.organization_id == o.id)
            .count()
        )
        insights = (
            db.query(Insight)
            .filter(Insight.organization_id == o.id)
            .count()
        )
        pending_decisions = (
            db.query(Decision)
            .filter(
                Decision.organization_id == o.id,
                Decision.status == DecisionStatus.PENDING,
            )
            .count()
        )

        total_users += users
        total_workspaces += workspaces
        total_modules += modules
        total_engagements += engagements
        total_insights += insights
        total_findings += findings
        total_pending_decisions += pending_decisions

        clients.append({
            "id": o.id,
            "name": o.name,
            "slug": o.slug,
            "created_at": o.created_at,
            "user_count": users,
            "workspace_count": workspaces,
            "enabled_module_count": modules,
            "engagement_count": engagements,
            "insight_count": insights,
            "finding_count": findings,
            "pending_decision_count": pending_decisions,
        })

    totals = {
        "client_count": len(orgs),
        "user_count": total_users,
        "workspace_count": total_workspaces,
        "enabled_module_count": total_modules,
        "engagement_count": total_engagements,
        "insight_count": total_insights,
        "finding_count": total_findings,
        "pending_decision_count": total_pending_decisions,
    }

    return {"totals": totals, "clients": clients}
