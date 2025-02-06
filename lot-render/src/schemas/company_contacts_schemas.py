from pydantic import BaseModel, Field
from account.src.schemas.contact_types_schemas import ContactTypeResponse


class CompanyContactResponse(BaseModel):
    id: int
    value: str
    type: ContactTypeResponse


class CompanyContactUpdate(BaseModel):
    token: str = Field(min_length=6, max_length=6)
    contact_type_id: int
    new_contact: str
