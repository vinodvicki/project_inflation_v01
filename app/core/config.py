import os

# Database Configuration
# For SQLite, DATABASE_URL will be like: sqlite:///./your_database_name.db
# The "./" means it will be created in the project root.
# You might want to place it inside an 'instance' folder or similar.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./career_pilot.db")

# Other application settings can go here
# Example:
# SECRET_KEY = os.getenv("SECRET_KEY", "a-very-secret-key-for-dev")
# API_V1_PREFIX = "/api/v1"

class Settings:
    PROJECT_NAME: str = "Career Co-Pilot API"
    DATABASE_URL: str = DATABASE_URL
    # Add other settings here as needed

settings = Settings()
