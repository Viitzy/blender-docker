from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import tempfile
from pathlib import Path
import subprocess
import os
from pydantic import BaseModel
from datetime import datetime
import json

from ..services.lots.analyze_lot_service import analyze_lot_service

router = APIRouter(tags=["lots"])


class LotAnalysisRequest(BaseModel):
    latitude: float
    longitude: float
    zoom: int = 20
    confidence: float = 0.62


class LotAnalysisResponse(BaseModel):
    id: str
    status: str
    results: dict | None = None
    error: str | None = None


@router.post(
    "/render/", description="Upload a CSV file and get back a rendered 3D model"
)
async def render_lot(csv_file: UploadFile = File(...)):
    """
    Upload a CSV file with lot points and get back a rendered 3D model.
    The CSV should contain columns: x, y, z (optional)
    """
    if not csv_file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded CSV
            temp_csv = Path(temp_dir) / "input.csv"
            with open(temp_csv, "wb") as f:
                content = await csv_file.read()
                f.write(content)

            # Set output path
            output_path = Path(temp_dir) / "output.glb"

            # Get Blender path from environment
            blender_path = os.getenv(
                "BLENDER_PATH", "/usr/local/blender/blender"
            )
            script_path = Path(__file__).parent.parent / "render_lot.py"

            # Run Blender to render the lot
            cmd = [
                blender_path,
                "--background",
                "--python",
                str(script_path),
                "--",
                str(temp_csv),
                str(output_path),
            ]

            subprocess.run(cmd, check=True)

            # Return the rendered file
            return FileResponse(
                path=output_path,
                filename="rendered_lot.glb",
                media_type="model/gltf-binary",
            )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, detail=f"Error rendering lot: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        )


@router.get("/health/", description="Health check endpoint")
async def health_check():
    """Check if the rendering service is healthy"""
    return {"status": "healthy", "message": "Lot rendering service is running"}


@router.post("/analyze/", response_model=LotAnalysisResponse)
async def analyze_lot(request: LotAnalysisRequest):
    """
    Analyze a lot based on its coordinates using satellite imagery and AI detection.
    The analysis includes:
    1. Satellite image acquisition
    2. Lot detection
    3. Area calculation
    4. Site image processing
    5. Color processing
    6. Elevation processing
    7. UTM coordinate conversion
    """
    result = await analyze_lot_service(
        latitude=request.latitude,
        longitude=request.longitude,
        zoom=request.zoom,
        confidence=request.confidence,
    )

    return LotAnalysisResponse(**result)
