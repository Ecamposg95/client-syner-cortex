"""Exhaustive verification of object visibility (Eje 3, Task Pack §4) and scope
(Eje 1), including the golden leak invariant:

    Ningún CLIENT_USER puede ver, bajo NINGUNA combinación de rol y estado, un
    objeto en estado interno ni de otra organización.
"""
import itertools
import pytest

from app.policy import roles as R
from app.policy.principal import Principal
from app.policy.visibility import ObjectType, is_visible, CLIENT_VISIBLE_STATES
from app.policy.engine import authorize, can_view
from app.policy.actions import Action

ORG = 10
OTHER_ORG = 20

# A broad pool of internal states that must NEVER be client-visible.
INTERNAL_STATES = [
    "INTERNAL_ONLY", "DRAFT", "DRAFT_INTERNAL", "IN_PROGRESS",
    "AI_GENERATED", "CONSULTANT_REVIEW", "APPROVED", "ARCHIVED", "RESTRICTED",
    "INTERNAL", None,
]

CLIENT_ROLES = [
    R.CLIENT_OWNER, R.CLIENT_EXECUTIVE, R.CLIENT_MANAGER,
    R.CLIENT_CONTRIBUTOR, R.CLIENT_VIEWER,
]


def crew(role=R.SYNER_CONSULTANT):
    return Principal(user_id=1, user_type="SYNER_CREW", org_roles={ORG: role})


def superadmin():
    return Principal(user_id=2, user_type="SYNER_CREW", is_superadmin=True, org_roles={})


def client(role, uid=3, org=ORG):
    return Principal(user_id=uid, user_type="CLIENT_USER", org_roles={org: role})


# ── Eje 3: client whitelist is exactly CLIENT_VISIBLE_STATES ────────────────

@pytest.mark.parametrize("object_type", list(ObjectType))
@pytest.mark.parametrize("role", CLIENT_ROLES)
def test_client_sees_only_whitelisted_states(object_type, role):
    p = client(role)
    visible = CLIENT_VISIBLE_STATES[object_type]
    for state in visible:
        # Own-only / executive-only nuances tested separately; here grant both.
        ok = is_visible(p, object_type, state, owner_id=p.user_id, org_id=ORG)
        # EXECUTIVE_ONLY only for OWNER/EXEC — skip the negative here.
        if state == "EXECUTIVE_ONLY" and role not in R.CLIENT_EXECUTIVE_TIER:
            assert ok is False
        else:
            assert ok is True, f"{role} debería ver {object_type.value}/{state}"


@pytest.mark.parametrize("object_type", list(ObjectType))
@pytest.mark.parametrize("role", CLIENT_ROLES)
@pytest.mark.parametrize("state", INTERNAL_STATES)
def test_client_never_sees_internal_states(object_type, role, state):
    # Skip states that legitimately belong to the object's client whitelist.
    if state in CLIENT_VISIBLE_STATES[object_type]:
        pytest.skip("estado pertenece al whitelist de este tipo")
    p = client(role)
    assert is_visible(p, object_type, state, owner_id=p.user_id, org_id=ORG) is False


@pytest.mark.parametrize("object_type", list(ObjectType))
@pytest.mark.parametrize("state", INTERNAL_STATES + ["CLIENT_SHARED", "CLIENT_VISIBLE"])
def test_crew_and_superadmin_see_everything_in_scope(object_type, state):
    assert is_visible(crew(), object_type, state, org_id=ORG) is True
    assert is_visible(superadmin(), object_type, state, org_id=ORG) is True


# ── Own-only and executive-only nuances ─────────────────────────────────────

def test_client_upload_is_own_only():
    owner = client(R.CLIENT_CONTRIBUTOR, uid=3)
    other = client(R.CLIENT_CONTRIBUTOR, uid=99)
    # Owner sees their own upload; another client in the org does not.
    assert is_visible(owner, ObjectType.DOCUMENT, "CLIENT_UPLOAD", owner_id=3, org_id=ORG) is True
    assert is_visible(other, ObjectType.DOCUMENT, "CLIENT_UPLOAD", owner_id=3, org_id=ORG) is False


def test_executive_only_recommendation_gated_to_exec_tier():
    for role in (R.CLIENT_OWNER, R.CLIENT_EXECUTIVE):
        assert is_visible(client(role), ObjectType.RECOMMENDATION, "EXECUTIVE_ONLY", org_id=ORG) is True
    for role in (R.CLIENT_MANAGER, R.CLIENT_CONTRIBUTOR, R.CLIENT_VIEWER):
        assert is_visible(client(role), ObjectType.RECOMMENDATION, "EXECUTIVE_ONLY", org_id=ORG) is False


# ── Eje 1: cross-org isolation ──────────────────────────────────────────────

@pytest.mark.parametrize("object_type", list(ObjectType))
def test_client_cannot_view_other_org_even_when_shared(object_type):
    p = client(R.CLIENT_OWNER, org=ORG)
    shared = next(iter(CLIENT_VISIBLE_STATES[object_type]))
    # Same shared state, but the object lives in OTHER_ORG -> out of scope.
    assert can_view(p, object_type, shared, owner_id=p.user_id, org_id=OTHER_ORG) is False
    assert can_view(p, object_type, shared, owner_id=p.user_id, org_id=ORG) is True


def test_client_cannot_authorize_action_in_other_org():
    p = client(R.CLIENT_OWNER, org=ORG)
    assert authorize(p, Action.UPDATE_TASKS, ORG) is True
    assert authorize(p, Action.UPDATE_TASKS, OTHER_ORG) is False


def test_crew_authorizes_across_orgs():
    p = crew()
    assert authorize(p, Action.RUN_TOOLS, ORG) is True
    assert authorize(p, Action.RUN_TOOLS, OTHER_ORG) is True  # cross-client consulting


def test_client_cannot_run_tools_or_share():
    p = client(R.CLIENT_OWNER, org=ORG)
    assert authorize(p, Action.RUN_TOOLS, ORG) is False
    assert authorize(p, Action.SHARE_WITH_CLIENT, ORG) is False
    assert authorize(p, Action.CREATE_CLIENT, ORG) is False
