from pydantic import BaseModel
from typing import List


class TimezoneResponse(BaseModel):
    id: int
    name: str


class TimezoneListResponse(BaseModel):
    timezones: List[TimezoneResponse]
