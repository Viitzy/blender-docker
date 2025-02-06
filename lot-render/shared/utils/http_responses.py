from fastapi.responses import JSONResponse
from fastapi import status
import json
from typing import Any
from shared.utils.json_encoder import json_encoder


def success_response(data: Any):
    json_data = json.dumps(data, default=json_encoder)
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json.loads(json_data)
    )


def not_found_response(data: Any):
    json_data = json.dumps(data, default=json_encoder)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content=json.loads(json_data)
    )


def internal_server_error_response(data: Any):
    json_data = json.dumps(data, default=json_encoder)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=json.loads(json_data),
    )


def bad_request_response(data: Any):
    json_data = json.dumps(data, default=json_encoder)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=json.loads(json_data),
    )


def conflict_response(data: Any):
    json_data = json.dumps(data, default=json_encoder)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=json.loads(json_data),
    )


def generic_error_response(data: Any, status_code: int):
    json_data = json.dumps(data, default=json_encoder)
    return JSONResponse(
        status_code=status_code,
        content=json.loads(json_data),
    )
