from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Organization, OrganizationUser, User
from app.schemas.schemas import OrganizationCreate, OrganizationOut, OrganizationUserOut, OrganizationAddUser
from app.dependencies import get_current_active_user, get_organization_context, RoleChecker

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.get("", response_model=List[OrganizationUserOut])
def get_user_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all organizations the authenticated user belongs to.
    """
    # If superadmin, list all organizations
    if current_user.is_superadmin:
        orgs = db.query(Organization).all()
        # Map to OrganizationUser schema format
        return [
            OrganizationUser(
                id=o.id,
                organization_id=o.id,
                user_id=current_user.id,
                role="SUPERADMIN",
                organization=o
            )
            for o in orgs
        ]
        
    org_users = db.query(OrganizationUser).filter(OrganizationUser.user_id == current_user.id).all()
    return org_users

@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_in: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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

@router.get("/{x_organization_id}/users", response_model=List[Dict[str, Any]])
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

from typing import Dict, Any

@router.post("/{x_organization_id}/users", status_code=status.HTTP_201_CREATED)
def add_user_to_organization(
    member_in: OrganizationAddUser,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(["CLIENT_OWNER"]))
):
    """
    Add/Invite an existing user to the organization by email.
    """
    target_user = db.query(User).filter(User.email == member_in.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User with this email not found.")

    # Check if already a member
    existing = db.query(OrganizationUser).filter(
        OrganizationUser.organization_id == org_ctx.organization_id,
        OrganizationUser.user_id == target_user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this organization.")

    org_user = OrganizationUser(
        organization_id=org_ctx.organization_id,
        user_id=target_user.id,
        role=member_in.role
    )
    db.add(org_user)
    db.commit()
    return {"message": f"Successfully added {member_in.email} as {member_in.role}"}
