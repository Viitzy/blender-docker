from pydantic import BaseModel


class PaginationSchema(BaseModel):
    total_count: int
    page: int
    per_page: int
    returned_count: int
