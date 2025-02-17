from fastapi import FastAPI, status, Request, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from src.routers import lots
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import os


API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "x-api-key"

app = FastAPI(title="Lot Render API")

# Allow any origin with "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.middleware("http")
# async def check_api_key(request: Request, call_next):
#     if (
#         request.url.path.startswith("/docs")
#         or request.url.path.startswith("/redoc")
#         or request.url.path == "/openapi.json"
#         or request.method == "OPTIONS"
#     ):
#         return await call_next(request)

#     api_key = request.headers.get("X-API-Key")
#     if not api_key:
#         return JSONResponse(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             content={"detail": "Missing API key"},
#         )

#     if api_key not in [API_KEY]:
#         return JSONResponse(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             content={"detail": "Invalid API key"},
#         )

#     return await call_next(request)


api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


# async def get_api_key(api_key_header: str = Security(api_key_header)):
#     if api_key_header in [
#         API_KEY,
#     ]:
#         return api_key_header
#     else:
#         raise HTTPException(
#             status_code=HTTP_403_FORBIDDEN,
#             detail="Could not validate credentials",
#         )


app.include_router(lots.router, prefix="/lots")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
