"""Canonical role identifiers (single source of truth).

Roles live on OrganizationUser.role as strings today; these constants exist so
no module hardcodes a role string (which caused drift like "CONSULTANT" vs
"SYNER_CONSULTANT"). Mirrors the canonical enums of the Task Pack §5.
"""

# ── Platform ───────────────────────────────────────────────────────────────
SUPERADMIN = "SUPERADMIN"  # Atlas Tech platform role — above every commercial role.

# ── Syner crew (internal) ──────────────────────────────────────────────────
SYNER_ADMIN = "SYNER_ADMIN"
SYNER_PARTNER = "SYNER_PARTNER"
SYNER_CONSULTANT = "SYNER_CONSULTANT"
SYNER_ANALYST = "SYNER_ANALYST"
SYNER_PM = "SYNER_PM"
SYNER_VIEWER = "SYNER_VIEWER"

# ── Client (external) ──────────────────────────────────────────────────────
CLIENT_OWNER = "CLIENT_OWNER"
CLIENT_EXECUTIVE = "CLIENT_EXECUTIVE"
CLIENT_MANAGER = "CLIENT_MANAGER"
CLIENT_CONTRIBUTOR = "CLIENT_CONTRIBUTOR"
CLIENT_VIEWER = "CLIENT_VIEWER"

SYNER_ROLES = frozenset({
    SUPERADMIN, SYNER_ADMIN, SYNER_PARTNER, SYNER_CONSULTANT,
    SYNER_ANALYST, SYNER_PM, SYNER_VIEWER,
})
CLIENT_ROLES = frozenset({
    CLIENT_OWNER, CLIENT_EXECUTIVE, CLIENT_MANAGER, CLIENT_CONTRIBUTOR, CLIENT_VIEWER,
})
ALL_ROLES = SYNER_ROLES | CLIENT_ROLES

# Client roles allowed to see EXECUTIVE_ONLY recommendations (Task Pack §4).
CLIENT_EXECUTIVE_TIER = frozenset({CLIENT_OWNER, CLIENT_EXECUTIVE})


def is_syner_role(role: str) -> bool:
    return role in SYNER_ROLES


def is_client_role(role: str) -> bool:
    return role in CLIENT_ROLES
