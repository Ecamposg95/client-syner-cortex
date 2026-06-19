"""Client-facing portal endpoints: an aggregated consultancy status summary.

This is the client's surface, so it must be hermetic: a CLIENT_USER may only ever
read their own organization, and only the client-visible state of each artifact.

Eje 1 (scope) is enforced here by get_organization_context, which validates that
the caller is a member of the org named in X-Organization-ID (crew/superadmin may
cross into any org; a CLIENT_USER cannot). The principal is also resolved so the
service can reason about visibility per the policy whitelist.

Eje 3 (object visibility) is applied inside app/services/portal/summary_service.py.
That service is OUT OF SCOPE for this change, but for the record it currently
filters Diagnosis, Roadmap, RoadmapItem and Document for clients via a local
CLIENT_VISIBLE set. It does NOT yet narrow the following for client users, which
is the remaining leak surface to close in the service:

  - Finding   (critical_findings): returned for any engagement regardless of an
                internal/client visibility flag — a client sees all CRITICAL/HIGH
                findings, including internal-only ones.
  - Decision  (open_decisions): all PENDING decisions are returned unfiltered.
  - Deliverable (deliverables.engagement_by_status): counted by status with no
                visibility narrowing.
  - KPI       (kpis): returned wholesale.

TODO(service): in summary_service.build_summary, route the client path through
the policy layer — prefer policy.deps.scoped_query(..., object_type=ObjectType.*)
for models that carry a `visibility` column, and pass the Principal so crew keep
full scope while clients are whitelisted. Replace the ad-hoc CLIENT_VISIBLE set
with app.policy.visibility.client_visible_states to avoid drift from §4.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_organization_context
from app.models.models import OrganizationUser
from app.policy.deps import get_principal
from app.policy.principal import Principal
from app.services.portal.summary_service import build_summary

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/summary")
def get_portal_summary(
    db: Session = Depends(get_db),
    # Eje 1: validates membership in the org from X-Organization-ID (403 otherwise).
    org_ctx: OrganizationUser = Depends(get_organization_context),
    # Resolved so callers/services can apply Eje 3 visibility consistently. Kept
    # here even though build_summary still derives client-ness from the User, so
    # the principal is available the moment the service adopts the policy layer.
    principal: Principal = Depends(get_principal),
):
    """Aggregated status of the consultancy engagement for the active organization.

    Response shape is unchanged (the Vite client depends on it); only WHICH rows
    are visible is governed by policy. Client visibility narrowing for the
    aggregated reads happens in build_summary (see module docstring for the gaps
    still to close there)."""
    return build_summary(db, org_ctx.organization_id, org_ctx.user)
