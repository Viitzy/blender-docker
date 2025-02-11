from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import tempfile
from pathlib import Path
import subprocess
import os
from pydantic import BaseModel
from datetime import datetime
import json
from typing import Optional, Dict, Any

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
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


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
    )

    return LotAnalysisResponse(**result)
