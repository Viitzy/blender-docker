from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from account.src.schemas.addresses_schemas import AddressResponse
from account.src.schemas.company_types_schemas import CompanyTypeResponse
from account.src.schemas.company_contacts_schemas import CompanyContactResponse


class CompanyResponse(BaseModel):
    id: int
    name: str
    cnpj: Optional[str]
    company_type: CompanyTypeResponse
    website: Optional[str]
    href: Optional[str]
    creci: Optional[str]
    contacts: Optional[list[CompanyContactResponse]] = None
    address: Optional[AddressResponse] = None
    created_at: datetime
    updated_at: Optional[datetime]


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    cnpj: Optional[str] = None
    website: Optional[str] = None
    creci: Optional[str] = None


class CompanyUpdateResponse(BaseModel):
    message: str
