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
    zoom: int = 20
    confidence: float = 0.62
    object_id: Optional[str] = None
    street_name: Optional[str] = None
    year: Optional[str] = None


class DetectLotResponse(BaseModel):
    id: str
    status: str
    points: List[Point]
    error: Optional[str] = None


class ProcessLotRequest(BaseModel):
    doc_id: str
    points: List[Point]
    zoom: int = 20
    confidence: float = 0.62


class ProcessLotResponse(BaseModel):
    id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/detect/", response_model=DetectLotResponse)
async def detect_lot(request: DetectLotRequest):
    """
    Detect a lot based on its coordinates using satellite imagery and AI detection.
    Returns only the detected polygon points.
    """
    result = await detect_lot_service(
        latitude=request.latitude,
        longitude=request.longitude,
        zoom=request.zoom,
        confidence=request.confidence,
        object_id=request.object_id,
        year=request.year,
    )

    return DetectLotResponse(**result)


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
        zoom=request.zoom,
        confidence=request.confidence,
    )

    return ProcessLotResponse(**result)
