import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Boolean, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import enum

from app.db import Base

class ProficiencyLevelEnum(str, enum.Enum):
    beginner = "Beginner"
    intermediate = "Intermediate"
    advanced = "Advanced"
    expert = "Expert"

class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    skill_name = Column(String, nullable=False, index=True)

    proficiency_level = Column(SQLAlchemyEnum(ProficiencyLevelEnum), nullable=True)
    is_top_skill = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to User
    user = relationship("User", back_populates="skills")

    # Using default SQLAlchemy __init__ is fine here.
    # For skill_name, we might want to ensure .strip() is called before saving.
    # This can be handled by a Pydantic model during API input, or a @validates decorator in SQLAlchemy.
    # For simplicity here, we assume input is cleaned or will add @validates later if needed.

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "skill_name": self.skill_name,
            "proficiency_level": self.proficiency_level.value if self.proficiency_level else None,
            "is_top_skill": self.is_top_skill,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<UserSkill id='{self.id}' user_id='{self.user_id}' skill_name='{self.skill_name}'>"
