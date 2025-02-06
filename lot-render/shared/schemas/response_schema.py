from pydantic import BaseModel, validator
from typing import Any, Generic, Literal, Optional, Type, TypeVar
from shared.schemas.pagination_schemas import PaginationSchema

T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    status: Literal["success", "error"]
    message: Optional[str] = None
    data: Optional[T] = None
    meta: Optional[PaginationSchema] = None

    class Config:
        validate_assignment = True
