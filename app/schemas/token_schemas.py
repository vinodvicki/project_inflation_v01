from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    # 'sub' (subject) is a standard JWT claim for the user identifier.
    # We'll store the user_id (which is a string UUID) here.
    sub: Optional[str] = None
    # You can add other claims like 'exp' (expiration time) if needed.
