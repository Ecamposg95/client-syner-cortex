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
from sqlalchemy import Enum as SAEnum, and_, or_
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


def _enum_class_of(model, column_name: str):
    """Return the Python Enum class backing `model.<column_name>` if that column
    is a SQLAlchemy Enum mapped to a `enum.Enum`, else None.

    We inspect the mapped table column type rather than the InstrumentedAttribute
    so this stays generic for any model (ToolRun, Report, …), not hardcoded.
    """
    try:
        col_type = model.__table__.c[column_name].type
    except (AttributeError, KeyError):
        return None
    if isinstance(col_type, SAEnum):
        # SAEnum.enum_class is set when the type was built from a Python enum.
        enum_cls = getattr(col_type, "enum_class", None)
        if enum_cls is not None:
            return enum_cls
    return None


def _translate_states(states, enum_cls):
    """Map a set of whitelist strings to members of `enum_cls`.

    A string matches a member by `.name` or `.value`. Strings with no matching
    member are silently dropped: the whitelist is shared across object types and
    may legitimately name states a given enum doesn't define. Dropping (rather
    than raising) keeps scoped_query fail-closed — an unknown state simply can't
    widen the result set.
    """
    by_name = {m.name: m for m in enum_cls}
    by_value = {m.value: m for m in enum_cls}
    out = set()
    for s in states:
        member = by_name.get(s) or by_value.get(s)
        if member is not None:
            out.add(member)
    return out


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

    # If `visibility` is a SQLAlchemy Enum column (e.g. ToolRun.visibility ->
    # Visibility), comparing against bare strings is unreliable: SQLAlchemy may
    # bind/compare against the enum *name*, so `.in_(["CLIENT_SHARED", ...])`
    # can silently match nothing (empty result) or, worse, the wrong rows.
    # Translate the whitelist strings to actual enum members first. For plain
    # String columns (e.g. Document.visibility) we keep comparing strings.
    enum_cls = _enum_class_of(model, "visibility")
    if enum_cls is not None:
        shared = _translate_states(shared, enum_cls)
        own_only = _translate_states(own_only, enum_cls)

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
