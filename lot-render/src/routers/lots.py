from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import tempfile
from pathlib import Path
import subprocess
import os

router = APIRouter(tags=["lots"])


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
