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
        from app.core.auth import get_password_hash # Local import to avoid circular dependency at module level

        super().__init__(email=email.lower(), first_name=first_name, last_name=last_name, **kwargs)
        if 'id' not in kwargs and not self.id: # Ensure id is set if not loaded or already defaulted by SA
             self.id = str(uuid.uuid4())
        self.password_hash = get_password_hash(password) # Use passlib for hashing

    # set_password is no longer needed as hashing is done in __init__ via get_password_hash
    # If password changes are allowed post-creation, a method like this would be needed:
    # def set_password(self, password: str):
    #     from app.core.auth import get_password_hash
    #     self.password_hash = get_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Checks if the provided password matches the stored passlib hash."""
        from app.core.auth import verify_password # Local import
        if not self.password_hash:
            return False
        return verify_password(password, self.password_hash)

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
