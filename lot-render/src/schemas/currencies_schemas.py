from pydantic import BaseModel
from typing import List


class CurrencyResponse(BaseModel):
    id: int
    name: str


class CurrenciesListResponse(BaseModel):
    currencies: List[CurrencyResponse]
