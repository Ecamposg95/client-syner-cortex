"""ROLE_CAPABILITIES — the single source of truth for role × action, encoding
the permission matrix of Task Pack §8 cell by cell.

Each cell is a Capability, not a bare bool, so the asterisk semantics survive:
  - ALLOW           "Sí"   — permitted outright.
  - DENY            "No"   — never permitted (default for unlisted cells).
  - CONDITIONAL     "Sí*"  — permitted only if a specific extra permission/flag is
                            granted (enforced by the caller's context).
  - CLIENT_APPROVAL "Sí**" — the client's own approval of a deliverable, NOT
                            internal Syner approval. Distinct lane from ALLOW.

SUPERADMIN sits above every row (handled in `capability()`), and any cell not
listed defaults to DENY — deny-by-default is the safe posture.
"""
import enum

from app.policy.actions import Action
from app.policy import roles as R


class Capability(str, enum.Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    CONDITIONAL = "CONDITIONAL"
    CLIENT_APPROVAL = "CLIENT_APPROVAL"


_A = Capability.ALLOW
_C = Capability.CONDITIONAL
_K = Capability.CLIENT_APPROVAL

# CAPABILITY_MATRIX[action][role] -> Capability. Unlisted (action, role) => DENY.
# Columns map: S.Admin=SYNER_ADMIN, Partner=SYNER_PARTNER, Consultant=SYNER_CONSULTANT,
# Analyst=SYNER_ANALYST, PM=SYNER_PM, then the five CLIENT_* roles.
CAPABILITY_MATRIX: dict[Action, dict[str, Capability]] = {
    Action.CREATE_CLIENT: {
        R.SYNER_ADMIN: _A,
    },
    Action.CREATE_WORKSPACE: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
    },
    Action.UPLOAD_INTERNAL_DOCS: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
        R.SYNER_ANALYST: _A, R.SYNER_PM: _A,
    },
    Action.UPLOAD_CLIENT_DOCS: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
        R.SYNER_ANALYST: _A, R.SYNER_PM: _A,
        R.CLIENT_OWNER: _A, R.CLIENT_EXECUTIVE: _A, R.CLIENT_MANAGER: _A,
        R.CLIENT_CONTRIBUTOR: _A,
    },
    Action.USE_INTERNAL_RAG: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
        R.SYNER_ANALYST: _A, R.SYNER_PM: _A,
    },
    Action.CLIENT_LIMITED_CHAT: {
        R.SYNER_ADMIN: _A,  # "Configura"
        R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
        R.CLIENT_OWNER: _C, R.CLIENT_EXECUTIVE: _C, R.CLIENT_MANAGER: _C,
    },
    Action.RUN_TOOLS: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
        R.SYNER_ANALYST: _C, R.SYNER_PM: _C,
    },
    Action.EDIT_AI_OUTPUTS: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
        R.SYNER_ANALYST: _C, R.SYNER_PM: _C,
    },
    Action.APPROVE_DELIVERABLES: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _C,
        R.CLIENT_OWNER: _K, R.CLIENT_EXECUTIVE: _K,
    },
    Action.SHARE_WITH_CLIENT: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
    },
    Action.VIEW_APPROVED_REPORTS: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
        R.SYNER_ANALYST: _A, R.SYNER_PM: _A,
        R.CLIENT_OWNER: _A, R.CLIENT_EXECUTIVE: _A, R.CLIENT_MANAGER: _C,
        R.CLIENT_CONTRIBUTOR: _C, R.CLIENT_VIEWER: _A,
        # Read-only internal viewer also sees approved reports.
        R.SYNER_VIEWER: _A,
    },
    Action.CREATE_ROADMAP: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
        R.SYNER_PM: _A,
    },
    Action.UPDATE_TASKS: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
        R.SYNER_ANALYST: _A, R.SYNER_PM: _A,
        R.CLIENT_OWNER: _C, R.CLIENT_EXECUTIVE: _C, R.CLIENT_MANAGER: _A,
        R.CLIENT_CONTRIBUTOR: _A,
    },
    Action.VIEW_INTERNAL_PLAYBOOKS: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _A, R.SYNER_CONSULTANT: _A,
        R.SYNER_ANALYST: _C, R.SYNER_PM: _C,
    },
    Action.VIEW_AUDIT: {
        R.SYNER_ADMIN: _A, R.SYNER_PARTNER: _C,
    },
    Action.CONFIGURE_MODULES: {
        R.SYNER_ADMIN: _A,
    },
}


def capability(role: str, action: Action) -> Capability:
    """The Capability for (role, action). SUPERADMIN gets ALLOW on everything;
    any unlisted cell is DENY (deny-by-default)."""
    if role == R.SUPERADMIN:
        return Capability.ALLOW
    return CAPABILITY_MATRIX.get(action, {}).get(role, Capability.DENY)


def is_allowed(role: str, action: Action, *, conditional_ok: bool = True) -> bool:
    """Boolean gate for an action. By default a CONDITIONAL cell counts as
    allowed at the policy gate (the extra condition is enforced in context);
    CLIENT_APPROVAL is its own lane and is NOT treated as a normal allow.
    Pass conditional_ok=False to require an unconditional ALLOW."""
    cap = capability(role, action)
    if cap is Capability.ALLOW:
        return True
    if cap is Capability.CONDITIONAL:
        return conditional_ok
    return False
