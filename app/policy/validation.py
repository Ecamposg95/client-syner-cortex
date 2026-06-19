"""Runtime validation of organization role strings.

Design decision — STRING + validation (NOT a Postgres Enum):
    Roles live on ``OrganizationUser.role`` as plain strings (see
    ``app.policy.roles``). We intentionally do NOT migrate the column to a
    Postgres ``ENUM`` type, because production already holds free-form role
    strings and an Enum migration would reject/break existing rows. Instead we
    keep the column as ``STRING`` and guard the *assignment points* (admin and
    organizations routers) with the helpers below, validating against the
    canonical set ``app.policy.roles.ALL_ROLES`` (Task Pack §5).

Use:
    * ``validate_org_role(role)`` — pure check; raises ``ValueError`` (no web
      coupling). Returns the role unchanged so it can be used inline.
    * ``assert_assignable(role)`` — same check but raises FastAPI
      ``HTTPException(400)`` for use directly inside request handlers.
"""
from __future__ import annotations

from fastapi import HTTPException

from app.policy import roles


def _valid_roles_msg() -> str:
    return f"Invalid role. Must be one of: {sorted(roles.ALL_ROLES)}"


def validate_org_role(role: str) -> str:
    """Validate that ``role`` is a canonical organization role.

    Returns the role unchanged when valid; raises ``ValueError`` otherwise
    (including for ``None`` / empty string). Use this in non-HTTP contexts or
    when you want to translate the error yourself.
    """
    if not role or role not in roles.ALL_ROLES:
        raise ValueError(_valid_roles_msg())
    return role


def assert_assignable(role: str) -> str:
    """Validate an assignable role inside a request handler.

    Same semantics as :func:`validate_org_role` but raises a FastAPI
    ``HTTPException`` with status 400, so callers in routers can use it without
    catching ``ValueError``. Returns the role unchanged when valid.
    """
    try:
        return validate_org_role(role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
