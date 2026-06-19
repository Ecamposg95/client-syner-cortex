"""Exhaustive verification of the capability matrix against Task Pack §8.

EXPECTED below is transcribed *independently* from the §8 table so this test is a
real cross-check of capabilities.py, not a tautology. Every (action, role) cell
is asserted — including the No/DENY cells — plus SUPERADMIN and SYNER_VIEWER.
"""
import pytest

from app.policy.actions import Action
from app.policy import roles as R
from app.policy.capabilities import Capability, capability

A, D, C, K = (
    Capability.ALLOW, Capability.DENY, Capability.CONDITIONAL, Capability.CLIENT_APPROVAL,
)

# Column order: S.Admin, Partner, Consultant, Analyst, PM,
#               C.Owner, C.Exec, C.Manager, Contributor, Viewer
COLS = [
    R.SYNER_ADMIN, R.SYNER_PARTNER, R.SYNER_CONSULTANT, R.SYNER_ANALYST, R.SYNER_PM,
    R.CLIENT_OWNER, R.CLIENT_EXECUTIVE, R.CLIENT_MANAGER, R.CLIENT_CONTRIBUTOR, R.CLIENT_VIEWER,
]

# Transcribed cell-by-cell from §8. "No/solicita" and "No/Sí*" worst-case -> as noted.
EXPECTED_ROWS: dict[Action, tuple] = {
    Action.CREATE_CLIENT:          (A, D, D, D, D, D, D, D, D, D),
    Action.CREATE_WORKSPACE:       (A, A, A, D, D, D, D, D, D, D),
    Action.UPLOAD_INTERNAL_DOCS:   (A, A, A, A, A, D, D, D, D, D),
    Action.UPLOAD_CLIENT_DOCS:     (A, A, A, A, A, A, A, A, A, D),
    Action.USE_INTERNAL_RAG:       (A, A, A, A, A, D, D, D, D, D),
    Action.CLIENT_LIMITED_CHAT:    (A, A, A, D, D, C, C, C, D, D),
    Action.RUN_TOOLS:              (A, A, A, C, C, D, D, D, D, D),
    Action.EDIT_AI_OUTPUTS:        (A, A, A, C, C, D, D, D, D, D),
    Action.APPROVE_DELIVERABLES:   (A, A, C, D, D, K, K, D, D, D),
    Action.SHARE_WITH_CLIENT:      (A, A, A, D, D, D, D, D, D, D),
    Action.VIEW_APPROVED_REPORTS:  (A, A, A, A, A, A, A, C, C, A),
    Action.CREATE_ROADMAP:         (A, A, A, D, A, D, D, D, D, D),
    Action.UPDATE_TASKS:           (A, A, A, A, A, C, C, A, A, D),
    Action.VIEW_INTERNAL_PLAYBOOKS:(A, A, A, C, C, D, D, D, D, D),
    Action.VIEW_AUDIT:             (A, C, D, D, D, D, D, D, D, D),
    Action.CONFIGURE_MODULES:      (A, D, D, D, D, D, D, D, D, D),
}

# SYNER_VIEWER is read-only (not a §8 column): only sees approved reports.
SYNER_VIEWER_EXPECTED: dict[Action, Capability] = {
    Action.VIEW_APPROVED_REPORTS: A,
}


def test_matrix_covers_every_action():
    assert set(EXPECTED_ROWS) == set(Action), "Matriz incompleta: faltan acciones"


@pytest.mark.parametrize("action", list(Action))
@pytest.mark.parametrize("col_index", range(len(COLS)))
def test_each_cell(action, col_index):
    role = COLS[col_index]
    expected = EXPECTED_ROWS[action][col_index]
    assert capability(role, action) == expected, (
        f"Celda incorrecta: {action.value} × {role} "
        f"=> {capability(role, action)} (esperado {expected})"
    )


@pytest.mark.parametrize("action", list(Action))
def test_superadmin_allows_everything(action):
    assert capability(R.SUPERADMIN, action) is Capability.ALLOW


@pytest.mark.parametrize("action", list(Action))
def test_syner_viewer_is_read_only(action):
    expected = SYNER_VIEWER_EXPECTED.get(action, Capability.DENY)
    assert capability(R.SYNER_VIEWER, action) == expected


@pytest.mark.parametrize("action", list(Action))
def test_unknown_role_denied_by_default(action):
    assert capability("NOT_A_ROLE", action) is Capability.DENY
