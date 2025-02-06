import os
import tempfile
import subprocess
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CSV to GLB Converter", version="1.0.0")


@app.post("/convert/csv-to-glb")
async def convert_csv_to_glb(csv_file: UploadFile):
    """
    Convert uploaded CSV file to GLB format using Blender
    """
    if not csv_file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded CSV
            csv_path = os.path.join(temp_dir, "input.csv")
            glb_path = os.path.join(temp_dir, "output.glb")

            # Save the uploaded file
            content = await csv_file.read()
            with open(csv_path, "wb") as f:
                f.write(content)

            # Get the path to the Blender executable from environment variable
            blender_path = os.environ.get("BLENDER_PATH", "blender")

            # Run the conversion script
            cmd = [
                blender_path,
                "--background",
                "--python",
                "scripts/csv_to_glb.py",
                "--",
                "--input",
                csv_path,
                "--output",
                glb_path,
            ]

            process = subprocess.run(cmd, capture_output=True, text=True)

            if process.returncode != 0:
                logger.error(f"Conversion failed: {process.stderr}")
                raise HTTPException(status_code=500, detail="Conversion failed")

            # Return the GLB file
            return FileResponse(
                glb_path,
                media_type="model/gltf-binary",
                filename=f"{os.path.splitext(csv_file.filename)[0]}.glb",
            )

    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)
