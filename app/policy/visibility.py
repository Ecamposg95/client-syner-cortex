"""Eje 3 — object-level visibility (Task Pack §4).

For a CLIENT_USER the visible set per object type is STRICT and whitelisted here.
Any internal state (INTERNAL_ONLY, DRAFT_*, AI_GENERATED, CONSULTANT_REVIEW, …)
is invisible to clients under every role/permission combination. Syner crew see
everything within their scope; the scope (which org) is Eje 1, handled elsewhere.
"""
import enum

from app.policy import roles as R


class ObjectType(str, enum.Enum):
    DOCUMENT = "DOCUMENT"
    REPORT = "REPORT"
    TOOLRUN = "TOOLRUN"
    ROADMAP_ITEM = "ROADMAP_ITEM"
    RECOMMENDATION = "RECOMMENDATION"


# States a CLIENT_USER may see, per object type. Everything else is internal.
CLIENT_VISIBLE_STATES: dict[ObjectType, frozenset[str]] = {
    ObjectType.DOCUMENT: frozenset({"CLIENT_SHARED", "CLIENT_UPLOAD"}),
    ObjectType.REPORT: frozenset({"CLIENT_SHARED"}),
    ObjectType.TOOLRUN: frozenset({"CLIENT_SHARED"}),
    ObjectType.ROADMAP_ITEM: frozenset({"CLIENT_VISIBLE", "CLIENT_ASSIGNED", "COMPLETED"}),
    ObjectType.RECOMMENDATION: frozenset({"SHARED", "EXECUTIVE_ONLY", "TASK_VISIBLE"}),
}

# States that, for a Document, are only the client's own (not any client's).
_OWN_ONLY_STATES: dict[ObjectType, frozenset[str]] = {
    ObjectType.DOCUMENT: frozenset({"CLIENT_UPLOAD"}),
}

# States gated to the client executive tier (OWNER/EXECUTIVE) only.
_EXECUTIVE_ONLY_STATES: dict[ObjectType, frozenset[str]] = {
    ObjectType.RECOMMENDATION: frozenset({"EXECUTIVE_ONLY"}),
}


def client_visible_states(object_type: ObjectType) -> frozenset[str]:
    return CLIENT_VISIBLE_STATES.get(object_type, frozenset())


def own_only_states(object_type: ObjectType) -> frozenset[str]:
    """States a client sees only for objects they own (e.g. their own upload)."""
    return _OWN_ONLY_STATES.get(object_type, frozenset())


def executive_only_states(object_type: ObjectType) -> frozenset[str]:
    """States gated to the client executive tier (OWNER/EXECUTIVE)."""
    return _EXECUTIVE_ONLY_STATES.get(object_type, frozenset())


def is_visible(
    principal,
    object_type: ObjectType,
    visibility: str | None,
    *,
    owner_id: int | None = None,
    org_id: int | None = None,
) -> bool:
    """Whether `principal` may see an object of `object_type` in state
    `visibility`. Crew see everything in scope; clients are whitelisted.

    `owner_id` is the object's creator/uploader (needed for own-only states like
    a client's CLIENT_UPLOAD). `org_id` is the object's organization (Eje 1 is
    enforced at query time, but passing it lets callers double-check tenancy)."""
    # Syner crew + superadmin: full visibility within scope.
    if principal.is_superadmin or principal.is_crew:
        return True

    allowed = client_visible_states(object_type)
    if visibility not in allowed:
        return False

    # Own-only states (e.g. a client's own upload) require ownership.
    if visibility in _OWN_ONLY_STATES.get(object_type, frozenset()):
        if owner_id is None or owner_id != principal.user_id:
            return False

    # Executive-tier-only states require the client to be OWNER/EXECUTIVE in org.
    if visibility in _EXECUTIVE_ONLY_STATES.get(object_type, frozenset()):
        role = principal.role_in(org_id) if org_id is not None else None
        if role not in R.CLIENT_EXECUTIVE_TIER:
            return False

    return True
