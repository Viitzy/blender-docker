from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import tempfile
from pathlib import Path
import subprocess
import os
from pydantic import BaseModel
from datetime import datetime
import json
from typing import Optional, Dict, Any, List

from ..services.lots.analyze_lot_service import analyze_lot_service
from ..services.lots.detect_lot_service import detect_lot_service
from ..services.lots.process_lot_service import process_lot_service

router = APIRouter(tags=["lots"])


class Point(BaseModel):
    lat: float
    lon: float


class DetectLotRequest(BaseModel):
    latitude: float
    longitude: float


class DetectLotData(BaseModel):
    points: List[Point]


class DetectLotResponse(BaseModel):
    status: str
    message: str
    data: Optional[DetectLotData]
    meta: Optional[Dict] = None


class ProcessLotRequest(BaseModel):
    doc_id: str
    points: List[Point]


class ProcessLotData(BaseModel):
    obj_id: str


class ProcessLotResponse(BaseModel):
    status: str
    message: str
    data: Optional[ProcessLotData]
    meta: Optional[Dict] = None


@router.post("/detect/", response_model=DetectLotResponse)
async def detect_lot(request: DetectLotRequest):
    """
    Detect a lot based on its coordinates using satellite imagery and AI detection.
    Returns only the detected polygon points.
    """
    result = await detect_lot_service(
        latitude=request.latitude,
        longitude=request.longitude,
        zoom=20,  # Fixed value
        confidence=0.62,  # Fixed value
    )

    # Convert the service response to the new format
    if result["status"] == "success":
        points = [Point(**point) for point in result["points"]]
        return DetectLotResponse(
            status="success",
            message="Success",
            data=DetectLotData(points=points),
            meta=result.get("meta"),
        )
    else:
        return DetectLotResponse(
            status="error",
            message=result.get("error", "An error occurred"),
            data=None,
            meta=result.get("meta"),
        )


@router.post("/process/", response_model=ProcessLotResponse)
async def process_lot(request: ProcessLotRequest):
    """
    Process a lot based on its polygon points.
    Executes the complete analysis pipeline including:
    1. Area calculation
    2. Site image processing
    3. Color processing
    4. Elevation processing
    5. UTM coordinate conversion
    6. Cardinal points
    7. Front points
    8. CSV generation
    9. GLB generation
    10. Slope classification
    """
    result = await process_lot_service(
        doc_id=request.doc_id,
        points=request.points,
        zoom=20,  # Fixed value
        confidence=0.62,  # Fixed value
    )

    if result["status"] == "success":
        return ProcessLotResponse(
            status="success",
            message="Success",
            data=ProcessLotData(obj_id=result["doc_id"]),
            meta=None,
        )
    else:
        return ProcessLotResponse(
            status="error",
            message=result.get("error", "An error occurred"),
            data=None,
            meta=None,
        )
