import uuid
import hashlib
from datetime import datetime # Keep for type hinting if needed, but SQLAlchemy handles actual tz
import pytz # Good for timezone definitions, though func.now() on DB is often better

from sqlalchemy import Column, String, DateTime, func
# from sqlalchemy.dialects.postgresql import UUID # Alternative for PostgreSQL
from sqlalchemy.orm import relationship

from app.db import Base # Import Base from db.py

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    # Use timezone=True for DateTime to store timezone-aware datetimes.
    # server_default=func.now() uses the database's current time.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    compensations = relationship("Compensation", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")

    # The __init__ can be simplified or even omitted if default SQLAlchemy behavior is fine,
    # but we need it for password hashing and email lowercasing.
    # SQLAlchemy's __init__ by default accepts kwargs for column attributes.
    def __init__(self, email: str, password: str, first_name: str = "", last_name: str = "", **kwargs):
        # If 'id' is passed via kwargs (e.g. when loading from DB), SQLAlchemy handles it.
        # Otherwise, our default lambda for 'id' column will generate it.
        # We call super().__init__ to let SQLAlchemy handle its part.
        # We only explicitly set attributes that need special handling before DB commit.
        super().__init__(email=email.lower(), first_name=first_name, last_name=last_name, **kwargs)
        if 'id' not in kwargs: # If id is not being set from DB load
             self.id = str(uuid.uuid4()) # Ensure id is generated if not loaded
        self.set_password(password)
        # Note: created_at and updated_at are handled by the database via server_default/onupdate.
        # No need to set them in __init__ if using server_default.

    def set_password(self, password: str):
        """Hashes the password using SHA-256 with a salt."""
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
        self.password_hash = f"{salt}${hashed_password}"

    def check_password(self, password: str) -> bool:
        """Checks if the provided password matches the stored hash."""
        if not self.password_hash or '$' not in self.password_hash:
            return False
        salt, stored_hash_part = self.password_hash.split('$', 1)
        input_password_hash = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
        return input_password_hash == stored_hash_part

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the user, excluding sensitive data."""
        return {
            "id": str(self.id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            # Ensure created_at/updated_at are present before calling isoformat
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<User id='{self.id}' email='{self.email}'>"
