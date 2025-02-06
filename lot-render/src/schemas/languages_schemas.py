from pydantic import BaseModel
from typing import List


class LanguageResponse(BaseModel):
    id: int
    name: str


class LanguagesListResponse(BaseModel):
    languages: List[LanguageResponse]
