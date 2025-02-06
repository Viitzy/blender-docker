from fastapi import FastAPI, Request, status, Security, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import os


from routers import (
    companies,
    contacts,
    contact_types,
    currencies,
    genders,
    languages,
    roles,
    timezones,
    users,
    user_status,
)

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "x-api-key"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def check_api_key(request: Request, call_next):
    if (
        request.url.path.startswith("/docs")
        or request.url.path.startswith("/redoc")
        or request.url.path == "/openapi.json"
        or request.method == "OPTIONS"
    ):
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if api_key != API_KEY:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing API key"},
        )

    return await call_next(request)


api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )


app.include_router(
    companies.router, prefix="/companies", dependencies=[Depends(get_api_key)]
)
app.include_router(
    contacts.router, prefix="/contacts", dependencies=[Depends(get_api_key)]
)
app.include_router(
    contact_types.router,
    prefix="/contact_types",
    dependencies=[Depends(get_api_key)],
)
app.include_router(
    currencies.router, prefix="/currencies", dependencies=[Depends(get_api_key)]
)
app.include_router(
    genders.router, prefix="/genders", dependencies=[Depends(get_api_key)]
)
app.include_router(
    languages.router, prefix="/languages", dependencies=[Depends(get_api_key)]
)
app.include_router(
    roles.router, prefix="/roles", dependencies=[Depends(get_api_key)]
)
app.include_router(
    timezones.router, prefix="/timezones", dependencies=[Depends(get_api_key)]
)
app.include_router(
    users.router, prefix="/users", dependencies=[Depends(get_api_key)]
)
app.include_router(
    user_status.router,
    prefix="/user_status",
    dependencies=[Depends(get_api_key)],
)
