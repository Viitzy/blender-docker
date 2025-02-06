from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from account.src.schemas.genders_schemas import GenderResponse
from account.src.schemas.person_contacts_schemas import PersonContactResponse


class PersonResponse(BaseModel):
    id: int
    name: str
    preferred_name: Optional[str]
    identification: Optional[str]
    birth_date: datetime
    profile_picture: Optional[str]
    gender: Optional[GenderResponse] = None
    contacts: Optional[list[PersonContactResponse]]
    created_at: datetime
    updated_at: Optional[datetime]


class PersonUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=150)
    preferred_name: Optional[str] = Field(default=None, max_length=255)
    profile_picture: Optional[str] = Field(default=None, max_length=500)
    gender_id: Optional[int] = Field(default=None)
