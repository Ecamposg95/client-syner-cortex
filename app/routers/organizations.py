from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models.models import Organization, OrganizationUser, User
from app.schemas.schemas import OrganizationCreate, OrganizationOut, OrganizationUserOut, OrganizationAddUser
from app.dependencies import (
    get_current_active_user, get_organization_context, get_current_org_id, RoleChecker,
)
from app.policy import Action
from app.policy.deps import require_action

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.get("", response_model=List[OrganizationUserOut])
def get_user_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all organizations the authenticated user belongs to.
    """
    # Syner Crew (incl. superadmins) operate across the whole portfolio: they see
    # the Syner firm org plus every client org, not just rows they're linked to.
    # Their real membership role is honoured where it exists; otherwise crew act
    # as SYNER_PARTNER on clients (superadmins keep SUPERADMIN).
    if current_user.is_superadmin or current_user.user_type == "SYNER_CREW":
        memberships = {
            ou.organization_id: ou.role
            for ou in db.query(OrganizationUser).filter(
                OrganizationUser.user_id == current_user.id
            ).all()
        }
        default_role = "SUPERADMIN" if current_user.is_superadmin else "SYNER_PARTNER"
        orgs = db.query(Organization).all()
        return [
            OrganizationUser(
                id=o.id,
                organization_id=o.id,
                user_id=current_user.id,
                role=memberships.get(o.id, default_role),
                organization=o,
            )
            for o in orgs
        ]

    org_users = db.query(OrganizationUser).filter(OrganizationUser.user_id == current_user.id).all()
    return org_users

@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_in: OrganizationCreate,
    db: Session = Depends(get_db),
    # §8: CREATE_CLIENT is ALLOW only for SYNER_ADMIN (SUPERADMIN allow-all).
    # require_action gates ejes 1+2 against the X-Organization-ID header, so the
    # caller must resolve to SYNER_ADMIN in that org. Crew acting as the default
    # SYNER_PARTNER, and any CLIENT_* role, are denied (the old self-signup path
    # where any authenticated user could create an org is closed).
    _principal=Depends(require_action(Action.CREATE_CLIENT)),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new organization and make the creator CLIENT_OWNER.
    """
    import datetime
    # Unique slug generation
    slug_base = org_in.name.lower().replace(" ", "-")
    org_slug = f"{slug_base}-{current_user.id}-{int(datetime.datetime.utcnow().timestamp())}"
    
    org = Organization(name=org_in.name, slug=org_slug)
    db.add(org)
    db.flush()

    # Link user
    org_user = OrganizationUser(
        organization_id=org.id,
        user_id=current_user.id,
        role="CLIENT_OWNER"
    )
    db.add(org_user)
    db.commit()
    db.refresh(org)
    return org

@router.get("/users", response_model=List[Dict[str, Any]])
def get_organization_users(
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(["CLIENT_OWNER", "CLIENT_EXECUTIVE", "CONSULTANT"]))
):
    """
    List all users belonging to the active organization.
    """
    results = db.query(OrganizationUser, User).join(User, OrganizationUser.user_id == User.id).filter(
        OrganizationUser.organization_id == org_ctx.organization_id
    ).all()
    
    return [
        {
            "id": org_user.id,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": org_user.role,
            "created_at": org_user.created_at
        }
        for org_user, user in results
    ]

@router.post("/users", status_code=status.HTTP_201_CREATED)
def add_user_to_organization(
    member_in: OrganizationAddUser,
    db: Session = Depends(get_db),
    # §8: managing an org's membership is org administration → CONFIGURE_MODULES
    # (ALLOW only SYNER_ADMIN). This replaces RoleChecker(["CLIENT_OWNER"]); a
    # CLIENT_OWNER can no longer add members on their own.
    _principal=Depends(require_action(Action.CONFIGURE_MODULES)),
    # Validated org id (membership-checked, Eje 1) the new member is added to.
    organization_id: int = Depends(get_current_org_id),
):
    """
    Add/Invite an existing user to the organization by email.
    """
    target_user = db.query(User).filter(User.email == member_in.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User with this email not found.")

    # Check if already a member
    existing = db.query(OrganizationUser).filter(
        OrganizationUser.organization_id == organization_id,
        OrganizationUser.user_id == target_user.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this organization.")

    org_user = OrganizationUser(
        organization_id=organization_id,
        user_id=target_user.id,
        role=member_in.role
    )
    db.add(org_user)
    db.commit()
    return {"message": f"Successfully added {member_in.email} as {member_in.role}"}
