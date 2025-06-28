from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

# Import Enums from the SQLAlchemy models to ensure consistency
# This creates a dependency from schemas to models, which is acceptable in some patterns.
# Alternatively, redefine Enums here if strict separation is desired.
from app.models.compensation import BonusTypeEnum, EquityTypeEnum

class CompensationBase(BaseModel):
    salary_annual: float = Field(..., gt=0, description="Annual salary in base currency")
    bonus_type: Optional[BonusTypeEnum] = None
    bonus_value: Optional[float] = Field(None, ge=0, description="Bonus percentage (e.g., 10 for 10%) or fixed amount")

    equity_type: Optional[EquityTypeEnum] = None
    equity_value_annual: Optional[float] = Field(None, ge=0, description="Estimated annual value of equity")
    equity_details: Optional[str] = None

    retirement_match_percentage: Optional[float] = Field(None, ge=0, le=100, description="Employer 401k/retirement match percentage")
    health_premium_annual: Optional[float] = Field(None, ge=0, description="User's annual cost for health insurance premiums")

    as_of_date: Optional[datetime] = Field(default_factory=lambda: datetime.now(datetime.timezone.utc),
                                           description="Date this compensation package is effective from")

class CompensationCreate(CompensationBase):
    # user_id will be set based on the authenticated user in the endpoint, not passed in body
    pass

class CompensationRead(CompensationBase):
    id: uuid.UUID # Or str
    user_id: uuid.UUID # Or str

    # Calculated properties from the model can be included if desired
    annual_bonus_amount_calculated: float
    estimated_total_compensation_calculated: float

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        # Pydantic V2 needs this to correctly handle enums from SQLAlchemy if they are Python enums
        use_enum_values = True # Ensures enum members are serialized to their values (e.g., "percentage" not BonusTypeEnum.percentage)
