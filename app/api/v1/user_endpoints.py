from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session # Though not strictly needed if only returning current_user from auth

from app.db import get_db # Might be needed for other user endpoints later
from app.models.user import User as UserModel
from app.schemas.user_schemas import UserRead
from app.core.auth import get_current_active_user

router = APIRouter(
    prefix="/users", # All routes in this router will be /users/...
    tags=["Users"]    # Tag for OpenAPI docs
)

@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get current authenticated user's profile information.
    """
    # The current_user object obtained from get_current_active_user is already
    # the SQLAlchemy UserModel instance. FastAPI will automatically serialize it
    # using the UserRead Pydantic schema because of response_model=UserRead
    # and UserRead.Config.from_attributes = True.
    return current_user

from app.schemas.compensation_schemas import CompensationCreate, CompensationRead
from app.models.compensation import Compensation as CompensationModel
from fastapi import status # For status codes

@router.post("/me/compensations", response_model=CompensationRead, status_code=status.HTTP_201_CREATED)
async def create_user_compensation(
    compensation_in: CompensationCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create a new compensation record for the current authenticated user.
    """
    new_compensation = CompensationModel(
        **compensation_in.model_dump(exclude_unset=True), # Pass validated data, excluding unset optional fields
        user_id=current_user.id # Associate with the current user
    )

    db.add(new_compensation)
    try:
        db.commit()
        db.refresh(new_compensation)
    except Exception as e: # Catch potential DB errors (e.g., constraint violations if any)
        db.rollback()
        # Log the error e for debugging
        print(f"Error creating compensation: {e}") # Basic logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save compensation record."
        )

    return new_compensation # FastAPI serializes using CompensationRead

from app.schemas.skill_schemas import UserSkillCreate, UserSkillRead
from app.models.user_skill import UserSkill as UserSkillModel

@router.post("/me/skills", response_model=UserSkillRead, status_code=status.HTTP_201_CREATED)
async def create_user_skill(
    skill_in: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create a new skill record for the current authenticated user.
    """
    # Optional: Check for duplicate skill_name for the same user if desired
    # existing_skill = db.query(UserSkillModel).filter(
    #     UserSkillModel.user_id == current_user.id,
    #     UserSkillModel.skill_name.ilike(skill_in.skill_name) # Case-insensitive check
    # ).first()
    # if existing_skill:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"Skill '{skill_in.skill_name}' already exists for this user."
    #     )

    new_skill = UserSkillModel(
        **skill_in.model_dump(exclude_unset=True),
        user_id=current_user.id
    )

    db.add(new_skill)
    try:
        db.commit()
        db.refresh(new_skill)
    except Exception as e:
        db.rollback()
        print(f"Error creating skill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save skill record."
        )

    return new_skill # FastAPI serializes using UserSkillRead

from typing import List # For list response type hint

@router.get("/me/compensations", response_model=List[CompensationRead])
async def list_user_compensations(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    skip: int = 0, # For pagination
    limit: int = 100 # For pagination
):
    """
    Retrieve all compensation records for the current authenticated user.
    """
    compensations = (
        db.query(CompensationModel)
        .filter(CompensationModel.user_id == current_user.id)
        .order_by(CompensationModel.as_of_date.desc(), CompensationModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return compensations

@router.get("/me/skills", response_model=List[UserSkillRead])
async def list_user_skills(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    skip: int = 0, # For pagination
    limit: int = 100 # For pagination
):
    """
    Retrieve all skill records for the current authenticated user.
    """
    skills = (
        db.query(UserSkillModel)
        .filter(UserSkillModel.user_id == current_user.id)
        .order_by(UserSkillModel.skill_name) # Or by created_at, etc.
        .offset(skip)
        .limit(limit)
        .all()
    )
    return skills
