from pydantic import BaseModel
from typing import List


class RoleResponse(BaseModel):
    id: int
    name: str


class RolesListResponse(BaseModel):
    roles: List[RoleResponse]
