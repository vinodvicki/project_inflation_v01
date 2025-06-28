from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime
import uuid # For id field type hint

# Shared base model for user attributes
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# Schema for user creation (request model for registration)
class UserCreate(UserBase):
    password: constr(min_length=8) # Password must be at least 8 characters

# Schema for user login (request model for login)
# FastAPI's OAuth2PasswordRequestForm is often used directly for login,
# but defining this can be useful for other validation contexts or if not using form data.
class UserLogin(BaseModel):
    email: EmailStr # Typically 'username' in OAuth2PasswordRequestForm, but we'll use email
    password: str

# Schema for reading/returning user data (response model)
# This inherits from UserBase and adds fields that are safe to return.
class UserRead(UserBase):
    id: uuid.UUID # Or str, depending on how you want to represent it from DB
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Enables Pydantic to read data from ORM models (SQLAlchemy)
        # For example, if you return a SQLAlchemy User object, Pydantic will try to map its attributes.
        # Ensure your SQLAlchemy User model has 'id', 'email', 'first_name', 'last_name', 'created_at', 'updated_at'.
        # The ORM mode was previously `orm_mode = True` in Pydantic V1.
        # In Pydantic V2, it's `from_attributes = True`.
