from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    ship_id: Optional[int]
    venue_id: Optional[int]
    is_active: bool
    venue_name: Optional[str] = None
