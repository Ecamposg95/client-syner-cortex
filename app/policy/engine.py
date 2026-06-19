"""The policy engine — the backbone of Task Pack §4.

    puede_acceder(usuario, accion, objeto) =
          eje_1_alcance(usuario, objeto)      # org/workspace en el alcance
      AND eje_2_rol(rol(usuario), accion)      # la matriz §8
      AND eje_3_visibilidad(usuario, objeto)   # el estado del objeto lo expone

`authorize` covers ejes 1+2 (scope + role) for an action in an org. `can_view`
covers eje 3 (object visibility), and `can_access` is the full conjunction.
"""
from app.policy.actions import Action
from app.policy.capabilities import is_allowed
from app.policy.principal import Principal
from app.policy.visibility import ObjectType, is_visible


def authorize(
    principal: Principal,
    action: Action,
    org_id: int | None = None,
    *,
    conditional_ok: bool = True,
) -> bool:
    """Eje 1 (scope) + Eje 2 (role) for `action` in `org_id`."""
    if not principal.in_scope(org_id):
        return False
    role = principal.role_in(org_id)
    if role is None:
        return False
    return is_allowed(role, action, conditional_ok=conditional_ok)


def can_view(
    principal: Principal,
    object_type: ObjectType,
    visibility: str | None,
    *,
    owner_id: int | None = None,
    org_id: int | None = None,
) -> bool:
    """Eje 1 (scope) + Eje 3 (object visibility)."""
    if not principal.in_scope(org_id):
        return False
    return is_visible(
        principal, object_type, visibility, owner_id=owner_id, org_id=org_id
    )


def can_access(
    principal: Principal,
    action: Action,
    object_type: ObjectType,
    visibility: str | None,
    *,
    org_id: int | None = None,
    owner_id: int | None = None,
) -> bool:
    """Full three-axis conjunction for acting on a concrete object."""
    return authorize(principal, action, org_id) and can_view(
        principal, object_type, visibility, owner_id=owner_id, org_id=org_id
    )
