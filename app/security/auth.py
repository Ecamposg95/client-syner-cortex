import os
import datetime
from typing import Optional, Union, Any
from jose import jwt
import bcrypt

# JWT configuration settings
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_key_cortex_2026_syner")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours expiration for ease of use

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if the plain password matches the hashed password using bcrypt.
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """
    Generate a bcrypt hash of the password.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(subject: Union[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    Generate a JWT token with user identity subject and expiration.
    """
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[str]:
    """
    Decode a JWT token and extract the subject (user ID or email).
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.JWTError:
        return None
