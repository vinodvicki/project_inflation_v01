from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db # To fetch user from DB
from app.models.user import User as UserModel # SQLAlchemy User model
from app.schemas.token_schemas import TokenData # Pydantic schema for token payload

# Password Hashing Setup (using bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer scheme for token input
# tokenUrl will point to our login endpoint (e.g., "/api/v1/auth/login")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


# --- Password Utilities ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)


# --- JWT Token Utilities ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default expiration time from settings
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# --- User Authentication Dependency ---
async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UserModel: # Return the SQLAlchemy UserModel instance
    """
    Decodes JWT token, validates it, and retrieves the user from the database.
    Raises HTTPException if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub") # 'sub' claim typically holds the user identifier
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(sub=user_id)
    except JWTError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.id == token_data.sub).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel: # Return the SQLAlchemy UserModel instance
    """
    Dependency that gets the current user and checks if they are active.
    (Assuming UserModel has an `is_active` attribute, which it doesn't currently.
     For now, this is a passthrough, but could be enhanced if `is_active` is added to User model).
    """
    # if not current_user.is_active: # Add is_active to UserModel if needed
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Note: The UserForAuth class is no longer needed as get_current_user now returns UserModel.
# If a Pydantic schema is preferred for the dependency output, it would be:
# async def get_current_user_pydantic(...) -> UserReadSchema:
#     user_model = await get_current_user_db_instance(...)
#     return UserReadSchema.from_orm(user_model)
