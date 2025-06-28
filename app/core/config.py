import os

# Database Configuration
# For SQLite, DATABASE_URL will be like: sqlite:///./your_database_name.db
# The "./" means it will be created in the project root.
# You might want to place it inside an 'instance' folder or similar.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./career_pilot.db")

# JWT settings
# TODO: IMPORTANT - Generate a strong, random secret key for production and store it securely (e.g., env variable)
# For development, a fixed key is okay but not for production.
# Command to generate a good key: openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token validity period (e.g., 30 minutes)


# Other application settings can go here
API_V1_PREFIX = "/api/v1" # Already used in main.py implicitly by router prefix

class Settings:
    PROJECT_NAME: str = "Career Co-Pilot API"
    DATABASE_URL: str = DATABASE_URL

    # JWT Settings
    SECRET_KEY: str = SECRET_KEY
    ALGORITHM: str = ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = ACCESS_TOKEN_EXPIRE_MINUTES

    API_V1_PREFIX: str = API_V1_PREFIX
    # Add other settings here as needed

settings = Settings()
