from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from account.src.schemas.contact_types_schemas import ContactTypeResponse


class PersonContactUpdate(BaseModel):
    token: str = Field(min_length=6, max_length=6)
    contact_type_id: int
    new_contact: str


class PersonContactResponse(BaseModel):
    id: int
    value: str
    is_primary: Optional[bool] = Field(default=False)
    type: ContactTypeResponse
    created_at: datetime
    updated_at: Optional[datetime]


class PersonContactListResponse(BaseModel):
    person_contacts: list[PersonContactResponse]


class PersonContactDeleteResponse(BaseModel):
    message: str


class PersonContactUpdateResponse(BaseModel):
    message: str
