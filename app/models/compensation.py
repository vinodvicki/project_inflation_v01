import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, func, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import enum # For Python Enum

from app.db import Base

# Define Python Enums for fields that have a limited set of choices
class BonusTypeEnum(str, enum.Enum):
    percentage = "percentage"
    fixed = "fixed"

class EquityTypeEnum(str, enum.Enum): # Example, can be expanded
    rsu = "RSU"
    stock_options = "Stock Options"
    espp = "ESPP"
    other = "Other"

class Compensation(Base):
    __tablename__ = "compensations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    salary_annual = Column(Float, nullable=False)

    bonus_type = Column(SQLAlchemyEnum(BonusTypeEnum), nullable=True)
    bonus_value = Column(Float, nullable=True) # Percentage (e.g., 10 for 10%) or fixed dollar amount

    equity_type = Column(SQLAlchemyEnum(EquityTypeEnum), nullable=True)
    equity_value_annual = Column(Float, nullable=True) # Estimated annual value
    equity_details = Column(String, nullable=True)

    retirement_match_percentage = Column(Float, nullable=True, default=0.0)
    health_premium_annual = Column(Float, nullable=True, default=0.0) # User's annual cost

    as_of_date = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=datetime.timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to User
    user = relationship("User", back_populates="compensations")

    # The __init__ can often be omitted if using SQLAlchemy's default keyword-based constructor,
    # but we might want it for type conversions or specific defaults not handled by `default=` on Column.
    # For now, we'll rely on SQLAlchemy's default __init__ and direct attribute setting.
    # If specific logic like `float(salary_annual)` is needed upon creation before commit,
    # it's better handled in a Pydantic model for API input validation, or a factory function.

    @property
    def annual_bonus_amount(self) -> float:
        """Calculates the annual bonus amount."""
        if self.bonus_type == BonusTypeEnum.percentage and self.bonus_value is not None and self.salary_annual is not None:
            return self.salary_annual * (self.bonus_value / 100.0)
        elif self.bonus_type == BonusTypeEnum.fixed and self.bonus_value is not None:
            return self.bonus_value
        return 0.0

    @property
    def calculated_total_compensation(self) -> float:
        """Calculates an estimated total annual compensation."""
        total_comp = self.salary_annual if self.salary_annual is not None else 0.0
        total_comp += self.annual_bonus_amount # Use the property

        if self.equity_value_annual:
            total_comp += self.equity_value_annual

        if self.retirement_match_percentage is not None and self.retirement_match_percentage > 0 and self.salary_annual is not None:
            match_value = self.salary_annual * (self.retirement_match_percentage / 100.0)
            total_comp += match_value

        return total_comp

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "salary_annual": self.salary_annual,
            "bonus_type": self.bonus_type.value if self.bonus_type else None,
            "bonus_value": self.bonus_value,
            "annual_bonus_amount_calculated": self.annual_bonus_amount, # Use property
            "equity_type": self.equity_type.value if self.equity_type else None,
            "equity_value_annual": self.equity_value_annual,
            "equity_details": self.equity_details,
            "retirement_match_percentage": self.retirement_match_percentage,
            "health_premium_annual": self.health_premium_annual,
            "estimated_total_compensation_calculated": self.calculated_total_compensation, # Use property
            "as_of_date": self.as_of_date.isoformat() if self.as_of_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<Compensation id='{self.id}' user_id='{self.user_id}' salary={self.salary_annual} as_of='{self.as_of_date.strftime('%Y-%m-%d') if self.as_of_date else 'N/A'}'>"
