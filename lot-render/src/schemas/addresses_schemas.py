from pydantic import BaseModel
from typing import Optional


class CountryResponse(BaseModel):
    id: int
    name: str


class StateResponse(BaseModel):
    id: int
    name: str
    country: CountryResponse


class CityResponse(BaseModel):
    id: int
    name: str
    state: StateResponse


class AddressResponse(BaseModel):
    id: int
    street: Optional[str]
    number: Optional[int]
    complement: Optional[str]
    neighborhood: Optional[str]
    city: CityResponse
    formatted_address: Optional[str]
