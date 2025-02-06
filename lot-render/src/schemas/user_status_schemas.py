from typing import List
from pydantic import BaseModel


class UserStatusResponse(BaseModel):
    id: int
    name: str


class UserStatusListResponse(BaseModel):
    user_statuses: List[UserStatusResponse]
