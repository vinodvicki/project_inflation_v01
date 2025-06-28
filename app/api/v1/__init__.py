from fastapi import APIRouter

# Import endpoint modules here
from . import dashboard_endpoints

# Create an APIRouter for version 1 of the API
router = APIRouter(
    prefix="/v1", # All routes in this router will be prefixed with /v1
    tags=["v1"],  # Tag for OpenAPI documentation
)

# Include routers from endpoint modules
router.include_router(dashboard_endpoints.router, tags=["Dashboard"])
# Add other endpoint module routers here if you create more, e.g.:
# router.include_router(user_endpoints.router, prefix="/users", tags=["Users"])

# This 'router' instance will be imported by app/main.py
