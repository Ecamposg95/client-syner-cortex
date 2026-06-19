"""FastAPI integration for the policy engine (Fase 3, PR2 foundation).

Provides the three things endpoints need so authorization stops being ad-hoc:
  - get_principal:    resolve the Principal once per request.
  - require_action:   a dependency factory gating an endpoint on a §8 action.
  - scoped_query:     a repository-layer query already filtered by org scope
                      (Eje 1) AND object visibility (Eje 3) for the caller.

Endpoints should build list/detail queries through `scoped_query` instead of
`db.query(Model)`, so a correct guard can never be undone by an unfiltered query.
"""
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.models import User
from app.policy.actions import Action
from app.policy.engine import authorize
from app.policy.principal import Principal, build_principal
from app.policy.visibility import (
    ObjectType, client_visible_states, own_only_states,
)


def get_principal(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> Principal:
    return build_principal(db, user)


def _org_id_header(
    x_organization_id: int | None = Header(None, alias="X-Organization-ID"),
) -> int | None:
    return x_organization_id


def require_action(action: Action):
    """Dependency: allow the request only if the principal may perform `action`
    in the organization named by the X-Organization-ID header (ejes 1+2)."""
    def _dep(
        principal: Principal = Depends(get_principal),
        org_id: int | None = Depends(_org_id_header),
    ) -> Principal:
        if not authorize(principal, action, org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado para esta acción",
            )
        return principal
    return _dep


def scoped_query(
    db: Session,
    model,
    principal: Principal,
    org_id: int | None,
    *,
    object_type: ObjectType | None = None,
    owner_column=None,
):
    """A query over `model` filtered to the caller's scope and visibility.

    - Eje 1: filtered to `org_id` when the model carries `organization_id`.
    - Eje 3: for CLIENT_USERs, restricted to the client-visible states of
      `object_type`. Own-only states (e.g. CLIENT_UPLOAD) require `owner_column`
      to equal the caller. Crew/superadmin see everything in scope.
    """
    q = db.query(model)
    if org_id is not None and hasattr(model, "organization_id"):
        q = q.filter(model.organization_id == org_id)

    # Crew/superadmin: no per-object visibility narrowing.
    if principal.is_superadmin or principal.is_crew:
        return q
    # No object type or no visibility column => nothing to narrow.
    if object_type is None or not hasattr(model, "visibility"):
        return q

    visible = set(client_visible_states(object_type))
    own_only = set(own_only_states(object_type))
    shared = visible - own_only

    conditions = []
    if shared:
        conditions.append(model.visibility.in_(shared))
    if own_only and owner_column is not None:
        conditions.append(and_(model.visibility.in_(own_only), owner_column == principal.user_id))

    if conditions:
        q = q.filter(or_(*conditions))
    else:
        # Client with no visible states for this type -> empty result, never a leak.
        q = q.filter(model.id.is_(None))
    return q
