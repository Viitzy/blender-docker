from pydantic import BaseModel


class ContactTypeResponse(BaseModel):
    id: int
    name: str


class ContactTypeListResponse(BaseModel):
    contact_types: list[ContactTypeResponse]
