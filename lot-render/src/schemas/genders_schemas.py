from pydantic import BaseModel
from typing import List


class GenderResponse(BaseModel):
    id: int
    name: str


class GendersListResponse(BaseModel):
    genders: List[GenderResponse]
