from fastapi import APIRouter

# Import endpoint modules here
from . import dashboard_endpoints
from . import auth_endpoints
from . import user_endpoints # Import the new user endpoints module

# Create an APIRouter for version 1 of the API
router = APIRouter(
    prefix="/v1", # All routes in this router will be prefixed with /v1
    tags=["v1"],  # Tag for OpenAPI documentation
)

# Include routers from endpoint modules
router.include_router(auth_endpoints.router)
router.include_router(user_endpoints.router) # Mounted at /api/v1/users (prefix from user_endpoints.router)
router.include_router(dashboard_endpoints.router) # No prefix here, path defined in dashboard_endpoints

# This 'router' instance will be imported by app/main.py
