from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Organization, OrganizationUser
from app.security.auth import get_password_hash, verify_password, create_access_token
from app.schemas.schemas import UserCreate, UserOut, Token, LoginRequest, ChangePasswordRequest
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user and creates their default personal organization.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email address already exists."
        )

    # Hash the password and create the user.
    # Self-signup ALWAYS creates an external CLIENT_USER — never a SYNER_CREW.
    # Internal crew accounts are provisioned only by an existing crew member.
    hashed_pwd = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        user_type="CLIENT_USER",
        is_active=True
    )
    db.add(user)
    db.flush() # Yields user.id

    # Create default organization for the new user
    org_name = f"{user.full_name or 'Personal'}'s Workspace"
    org_slug = f"org-{user.id}-{int(datetime.datetime.utcnow().timestamp())}"
    org = Organization(name=org_name, slug=org_slug)
    db.add(org)
    db.flush()

    # Link user to organization as CLIENT_OWNER role
    org_user = OrganizationUser(
        organization_id=org.id,
        user_id=user.id,
        role="CLIENT_OWNER"
    )
    db.add(org_user)
    
    db.commit()
    db.refresh(user)
    return user

import datetime

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user via form data (OAuth2 standard, username = email).
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-json", response_model=Token)
def login_json(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user via JSON body (Vite React frontend friendly).
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get profile information of the currently authenticated user.
    """
    return current_user

@router.post("/change-password", response_model=UserOut)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Set a new password for the authenticated user and clear the
    must_change_password flag (used for first-login forced rotation).
    """
    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.must_change_password = False
    db.commit()
    db.refresh(current_user)
    return current_user
