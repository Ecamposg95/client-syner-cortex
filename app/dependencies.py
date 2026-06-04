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
    
    if not org_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization"
        )
        
    return org_user

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
        # SUPERADMIN role bypasses all role constraints
        if org_user.role == "SUPERADMIN":
            return org_user
            
        if org_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires one of the following roles: {', '.join(self.allowed_roles)}"
            )
        return org_user
