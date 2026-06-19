from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import User, OrganizationUser, Organization
from app.security.auth import decode_access_token

# OAuth2 scheme pointing to our login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to retrieve the currently logged in user by decoding the JWT token.
    Raises credentials exception if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exception
        
    try:
        user_id = int(subject)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure the current user is active.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_syner_crew(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency to ensure the current user belongs to the internal Syner Crew.
    """
    if current_user.user_type != "SYNER_CREW" and not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Syner Crew access required")
    return current_user

def get_current_organization_id(x_organization_id: int = Header(..., alias="X-Organization-ID")) -> int:
    """DEPRECATED: trusts the X-Organization-ID header without validating membership.
    Do NOT use on data-bearing endpoints — use get_current_org_id instead, which
    enforces that the caller actually belongs to the organization."""
    return x_organization_id

def get_organization_context(
    x_organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> OrganizationUser:
    """
    Dependency to validate organization context based on X-Organization-ID header.
    Verifies that the user belongs to the organization and yields their link record.
    Superadmins automatically bypass organization membership checks.
    """
    # Check if user is superadmin
    if current_user.is_superadmin:
        # Check if organization actually exists
        org = db.query(Organization).filter(Organization.id == x_organization_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Return a mock OrganizationUser link object with SUPERADMIN role
        return OrganizationUser(
            organization_id=x_organization_id,
            user_id=current_user.id,
            role="SUPERADMIN",
            organization=org,
            user=current_user
        )
    
    # Check if user is member of organization
    org_user = db.query(OrganizationUser).filter(
        OrganizationUser.organization_id == x_organization_id,
        OrganizationUser.user_id == current_user.id
    ).first()

    # Syner Crew consult ACROSS clients: they may enter any organization even
    # without an explicit membership row. Their real membership role is honoured
    # where it exists (e.g. in the Syner org); otherwise they act as SYNER_PARTNER
    # on the client. CLIENT_USERs still require explicit membership.
    if not org_user and current_user.user_type == "SYNER_CREW":
        org = db.query(Organization).filter(Organization.id == x_organization_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return OrganizationUser(
            organization_id=x_organization_id,
            user_id=current_user.id,
            role="SYNER_PARTNER",
            organization=org,
            user=current_user,
        )

    if not org_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization"
        )

    return org_user

def get_current_org_id(org_ctx: OrganizationUser = Depends(get_organization_context)) -> int:
    """Validated organization id for data-bearing endpoints. Ensures the caller is a
    member (or superadmin) of the org named in the X-Organization-ID header, then
    returns that organization_id. Replaces the unvalidated get_current_organization_id."""
    return org_ctx.organization_id

class RoleChecker:
    """
    RBAC dependency factory that validates the user's role in the organization.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        org_user: OrganizationUser = Depends(get_organization_context)
    ) -> OrganizationUser:
        # Prevent CLIENT_USER from ever assuming a SYNER role, regardless of database misconfiguration
        if org_user.user.user_type == "CLIENT_USER" and org_user.role.startswith("SYNER_"):
            raise HTTPException(status_code=403, detail="Invalid role assignment for Client User")

        # SUPERADMIN role bypasses all role constraints
        if org_user.role == "SUPERADMIN":
            return org_user
            
        if org_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires one of the following roles: {', '.join(self.allowed_roles)}"
            )
        return org_user

def apply_visibility_filter(query, current_user: User):
    """
    Applies visibility constraints to a SQLAlchemy query.
    If the user is a CLIENT_USER, they can only see CLIENT_SHARED, CLIENT_UPLOAD, APPROVED, or CLIENT_VISIBLE items.
    Note: The caller must ensure the query is for a model that has a `visibility` column.
    """
    if current_user.is_superadmin or current_user.user_type == "SYNER_CREW":
        return query
    
    model = query.column_descriptions[0]['entity']
    if hasattr(model, 'visibility'):
        return query.filter(model.visibility.in_(["CLIENT_SHARED", "CLIENT_UPLOAD", "APPROVED", "CLIENT_VISIBLE"]))
    return query
