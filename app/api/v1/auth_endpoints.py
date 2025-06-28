from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User as UserModel
from app.schemas.user_schemas import UserCreate, UserRead
# app.core.auth contains get_password_hash, but User model's __init__ calls it.

router = APIRouter(
    prefix="/auth", # All routes in this router will be /auth/...
    tags=["Authentication"] # Tag for OpenAPI docs
)

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user.
    """
    # Check if user with this email already exists
    existing_user = db.query(UserModel).filter(UserModel.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    # Create new user instance. Password hashing is handled in UserModel.__init__
    new_user = UserModel(
        email=user_in.email, # UserModel __init__ will lowercase it
        password=user_in.password, # UserModel __init__ will hash it
        first_name=user_in.first_name,
        last_name=user_in.last_name
    )

    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user) # Refresh to get DB-generated values like created_at, default id
    except Exception as e: # Catch potential DB errors
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {e}"
        )

    return new_user # Pydantic will automatically serialize this to UserRead schema
                    # due to response_model=UserRead and UserRead.Config.from_attributes = True


from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import verify_password, create_access_token
from app.schemas.token_schemas import Token

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.
    """
    # OAuth2PasswordRequestForm uses 'username' field for the identifier.
    # We are using email as the identifier.
    user_email = form_data.username.lower() # Ensure consistent casing for lookup
    user = db.query(UserModel).filter(UserModel.email == user_email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # Or 400 for "incorrect username or password"
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    # UserModel.check_password() now uses passlib's verify_password internally.
    if not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    # The 'sub' (subject) of the token should be the user's unique identifier (their ID).
    access_token_data = {"sub": str(user.id)}
    access_token = create_access_token(data=access_token_data)

    return {"access_token": access_token, "token_type": "bearer"}
