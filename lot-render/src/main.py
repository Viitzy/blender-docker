from fastapi import (
    FastAPI,
    Request,
    Security,
    HTTPException,
    Depends,
    UploadFile,
    File,
)
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from shared.database.connections import engine_properties
from shared.models.models import Base
import os
import subprocess
import tempfile
from pathlib import Path

from properties.src.routers.cities import router as cities_router
from properties.src.routers.lots import router as lots_router
from properties.src.routers.favorite_lots import router as favorite_lots_router
from properties.src.routers.condominiums import router as condominiums_router

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "x-api-key"

app = FastAPI(title="Lot Render API")

# Allow any origin with "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

BLENDER_PATH = os.getenv("BLENDER_PATH", "/usr/local/blender/blender")
SCRIPT_DIR = Path(__file__).parent


def render_lot(csv_path: str, output_path: str):
    """Render a lot using Blender"""
    blender_script = SCRIPT_DIR / "render_lot.py"

    cmd = [
        BLENDER_PATH,
        "--background",
        "--python",
        str(blender_script),
        "--",
        csv_path,
        output_path,
    ]

    subprocess.run(cmd, check=True)


@app.middleware("http")
async def check_api_key(request: Request, call_next):
    # Permitir solicitações OPTIONS passar sem verificação de API key
    if request.method == "OPTIONS":
        return await call_next(request)

    if request.url.path.startswith("/docs"):
        return await call_next(request)

    if request.url.path.startswith("/openapi.json"):
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if api_key != API_KEY:
        return JSONResponse(
            status_code=HTTP_403_FORBIDDEN,
            content={"detail": "API Key inválida"},
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


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine_properties)


app.include_router(
    cities_router, prefix="/cities", dependencies=[Depends(get_api_key)]
)
app.include_router(
    lots_router, prefix="/lots", dependencies=[Depends(get_api_key)]
)
app.include_router(
    favorite_lots_router,
    prefix="/favorite-lots",
    dependencies=[Depends(get_api_key)],
)
app.include_router(
    condominiums_router,
    prefix="/condominiums",
    dependencies=[Depends(get_api_key)],
)


@app.post("/render-lot/")
async def create_lot_render(csv_file: UploadFile = File(...)):
    """
    Upload a CSV file and get back a rendered 3D model
    """
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded CSV
        temp_csv = Path(temp_dir) / "input.csv"
        with open(temp_csv, "wb") as f:
            content = await csv_file.read()
            f.write(content)

        # Set output path
        output_path = Path(temp_dir) / "output.glb"

        # Render the lot
        render_lot(str(temp_csv), str(output_path))

        # Return the rendered file
        return FileResponse(
            path=output_path,
            filename="rendered_lot.glb",
            media_type="model/gltf-binary",
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
