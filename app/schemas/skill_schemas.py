from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

from app.models.user_skill import ProficiencyLevelEnum # Import Enum from model

class UserSkillBase(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=100)
    proficiency_level: Optional[ProficiencyLevelEnum] = None
    is_top_skill: Optional[bool] = True

class UserSkillCreate(UserSkillBase):
    # user_id will be set from the authenticated user in the endpoint
    pass

class UserSkillRead(UserSkillBase):
    id: uuid.UUID # Or str
    user_id: uuid.UUID # Or str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True # For proper enum serialization
