from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
import os
from starlette.status import HTTP_403_FORBIDDEN

API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
