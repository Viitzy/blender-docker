from pydantic import BaseModel


class CompanyTypeResponse(BaseModel):
    id: int
    name: str
