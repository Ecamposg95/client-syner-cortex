"""Unit tests for canonical org-role validation (Task Pack §5).

Verifies that:
  * every canonical role in ALL_ROLES is accepted (incl. the ones some code
    sets historically omitted: CLIENT_CONTRIBUTOR, SYNER_PM, SYNER_VIEWER);
  * junk / empty / None are rejected;
  * the admin router's local CLIENT_ROLES set now covers all canonical client
    roles (it previously dropped CLIENT_CONTRIBUTOR).
"""
import pytest
from fastapi import HTTPException

from app.policy import roles
from app.policy.validation import validate_org_role, assert_assignable


@pytest.mark.parametrize("role", sorted(roles.ALL_ROLES))
def test_validate_accepts_all_canonical_roles(role):
    assert validate_org_role(role) == role
    assert assert_assignable(role) == role


def test_validate_accepts_previously_omitted_roles():
    for role in ("CLIENT_CONTRIBUTOR", "SYNER_PM", "SYNER_VIEWER"):
        assert role in roles.ALL_ROLES
        assert validate_org_role(role) == role


@pytest.mark.parametrize("bad", ["FOO", "", None, "client_owner", "consultant"])
def test_validate_org_role_rejects_invalid(bad):
    with pytest.raises(ValueError):
        validate_org_role(bad)


@pytest.mark.parametrize("bad", ["FOO", "", None])
def test_assert_assignable_raises_http_400(bad):
    with pytest.raises(HTTPException) as exc_info:
        assert_assignable(bad)
    assert exc_info.value.status_code == 400
    # Error message lists the valid roles to guide the caller.
    assert "Must be one of" in exc_info.value.detail


def test_admin_client_roles_set_is_complete():
    """admin.CLIENT_ROLES must cover every canonical client role (regression:
    it used to omit CLIENT_CONTRIBUTOR)."""
    from app.routers import admin

    assert set(admin.CLIENT_ROLES) == set(roles.CLIENT_ROLES)
    assert "CLIENT_CONTRIBUTOR" in admin.CLIENT_ROLES
