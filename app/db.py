from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings # Import the settings

# Create SQLAlchemy engine
# The connect_args is specific to SQLite to enable foreign key constraints,
# which are not enabled by default in SQLite's Python driver.
engine_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False} # Required for SQLite when used with FastAPI/Flask in some cases

engine = create_engine(
    settings.DATABASE_URL,
    **engine_args
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()

# Dependency to get DB session (for FastAPI or similar frameworks)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create all tables in the database
# This should be called cautiously, ideally via a migration tool in production,
# or as part of an initial setup script.
def create_database_tables():
    # Import all models here before calling create_all
    # so that they are registered with SQLAlchemy's metadata.
    # This can feel a bit like magic, but it's how SQLAlchemy discovers tables.
    # Ensure all your model files are imported if they define tables.
    from app.models.user import User # noqa
    from app.models.compensation import Compensation # noqa
    from app.models.user_skill import UserSkill # noqa

    print(f"Creating database tables for {settings.DATABASE_URL}...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")

if __name__ == "__main__":
    # This allows running `python app/db.py` to create tables manually.
    print("Running database initialization script...")
    create_database_tables()
