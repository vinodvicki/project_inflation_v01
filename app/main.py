from fastapi import FastAPI
from app.api.v1 import router as api_v1_router # Will be defined shortly
from app.core.config import settings
from app.db import create_database_tables # For initial DB setup if needed

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for the Career Co-Pilot application, helping users understand their compensation and career steps.",
    version="0.1.0" # Can be dynamic later
)

# Include API routers
app.include_router(api_v1_router, prefix="/api") # All v1 routes will be under /api/v1

@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    - Create database tables (if they don't exist). This is suitable for development.
      For production, migrations (e.g. Alembic) are preferred.
    """
    print("Application startup...")
    # In a real app, you might connect to a database pool here if not using SQLAlchemy engine's implicit pooling.
    # For SQLite with SQLAlchemy, the engine handles connections as needed.

    # Create tables - useful for first run / dev.
    # Consider moving this to a separate CLI command for production.
    create_database_tables() # This was defined in app/db.py
    print("Database tables checked/created.")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    """
    print("Application shutdown...")
    # Clean up resources, e.g., close database connections if explicitly managed.

@app.get("/")
async def read_root():
    """
    Root endpoint for basic API health check or welcome message.
    """
    return {"message": f"Welcome to the {settings.PROJECT_NAME}"}

# To run this application (from the project root directory):
# uvicorn app.main:app --reload
