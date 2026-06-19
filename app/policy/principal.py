"""Principal — the authenticated identity plus its memberships, resolved once
per request and passed to the policy engine. Replaces ad-hoc per-endpoint
resolution of "who is this and what role do they have here".
"""
from dataclasses import dataclass, field

from app.policy import roles as R


@dataclass
class Principal:
    user_id: int
    user_type: str                       # SYNER_CREW | CLIENT_USER
    is_superadmin: bool = False
    # Effective role per organization id the user belongs to.
    org_roles: dict[int, str] = field(default_factory=dict)

    @property
    def is_crew(self) -> bool:
        return self.user_type == "SYNER_CREW"

    @property
    def is_client(self) -> bool:
        return self.user_type == "CLIENT_USER"

    def role_in(self, org_id: int | None) -> str | None:
        """The user's role in `org_id`. Crew without an explicit membership act
        as SYNER_PARTNER on a client org (consultants work across clients);
        superadmins act as SUPERADMIN everywhere."""
        if org_id is not None and org_id in self.org_roles:
            return self.org_roles[org_id]
        if self.is_superadmin:
            return R.SUPERADMIN
        if self.is_crew:
            return R.SYNER_PARTNER
        return None

    def in_scope(self, org_id: int | None) -> bool:
        """Eje 1 — is `org_id` within the user's reach? Crew/superadmin reach any
        org (cross-client consulting); clients only their own memberships."""
        if self.is_superadmin or self.is_crew:
            return True
        return org_id is not None and org_id in self.org_roles


def build_principal(db, user) -> Principal:
    """Resolve a Principal from a User row + its OrganizationUser memberships."""
    from app.models.models import OrganizationUser

    memberships = db.query(OrganizationUser).filter(
        OrganizationUser.user_id == user.id
    ).all()
    org_roles = {m.organization_id: m.role for m in memberships}
    return Principal(
        user_id=user.id,
        user_type=user.user_type,
        is_superadmin=bool(getattr(user, "is_superadmin", False)),
        org_roles=org_roles,
    )
