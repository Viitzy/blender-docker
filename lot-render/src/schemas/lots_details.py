from typing import Optional, List
from pydantic import BaseModel, Field, validator


# Pydantic Models
class LotData(BaseModel):
    lot_id: int
    title: str
    lot_area: float
    lot_address: str
    latitude: Optional[float]
    longitude: Optional[float]
    lot_price: float
    complete_address: str
    city: str
    state: str
    country: str
    neighborhood: str
    rating: int
    lot_images: str


class MetaData(BaseModel):
    pageIndex: int
    perPage: int
    totalCount: Optional[int]


class LotResponse(BaseModel):
    meta: MetaData
    data: List[LotData]


class PropertiesQueryParams(BaseModel):
    query: Optional[str] = Field(None, description="Search query string")
    south: Optional[float] = Field(
        None, description="Southern latitude boundary"
    )
    west: Optional[float] = Field(
        None, description="Western longitude boundary"
    )
    north: Optional[float] = Field(
        None, description="Northern latitude boundary"
    )
    east: Optional[float] = Field(
        None, description="Eastern longitude boundary"
    )
    skip: int = Field(
        0, ge=0, description="Number of records to skip for pagination"
    )
    limit: int = Field(
        30,
        gt=0,
        le=500,
        description="Maximum number of records to return (max 500)",
    )
    region_id: Optional[int] = Field(None, ge=0, description="Region ID filter")
    city_id: Optional[int] = Field(None, ge=0, description="City ID filter")
    category_id: int = Field(0, ge=0, description="Category ID filter")
    price_min: Optional[float] = Field(
        None, ge=0, description="Minimum price filter"
    )
    price_max: Optional[float] = Field(
        None, ge=0, description="Maximum price filter"
    )
    area_min: Optional[float] = Field(
        None, ge=0, description="Minimum area filter"
    )
    area_max: Optional[float] = Field(
        None, ge=0, description="Maximum area filter"
    )
    own_land: bool = Field(False, description="Filter for own land")
    only_condos: bool = Field(False, description="Filter for condominiums only")
    only_lands: bool = Field(False, description="Filter for lands only")

    @validator("price_max")
    def check_price_max(cls, v, values):
        price_min = values.get("price_min")
        if v is not None and price_min is not None and v < price_min:
            raise ValueError(
                "price_max must be greater than or equal to price_min"
            )
        return v

    @validator("area_max")
    def check_area_max(cls, v, values):
        area_min = values.get("area_min")
        if v is not None and area_min is not None and v < area_min:
            raise ValueError(
                "area_max must be greater than or equal to area_min"
            )
        return v
