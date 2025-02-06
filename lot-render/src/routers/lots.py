from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Union

from properties.src.services.lots import (
    get_lot_details_service,
    search_lots_relevant_locations_service,
    get_lot_list_service,
    get_lot_points_service,
    get_lot_volume_service,
    get_lots_histogram_service,
    get_lot_routes_service,
)
from properties.src.schemas.lots_schemas import (
    LotDetails,
    LotRelevantLocation,
    LotsQueryParams,
    LotHomePage,
    LotPoints,
    LotVolume,
    GeograficalPoint,
    GeograficalPointElevation,
    LotHistogramMatrix,
    LotHistogramMatrixParams,
    LotRouteParams,
    LotRoutesResponse,
)
from shared.database.db_session import (
    get_db_properties,
)
from shared.schemas.response_schema import ResponseSchema
from shared.utils.http_responses import (
    success_response,
    internal_server_error_response,
    generic_error_response,
)
from shared.utils.redis_cache import check_cache, set_cache
import json


router = APIRouter(tags=["lots"])


@router.get("/{lot_id}", response_model=ResponseSchema[LotDetails])
def get_lot(lot_id: int, db: Session = Depends(get_db_properties)):

    response = ResponseSchema(status="error", message="Error getting lot")
    try:
        lot_details = get_lot_details_service.execute(db, lot_id)

        response.status = "success"
        response.message = "Success"
        response.data = LotDetails(**lot_details)

        return success_response(response)
    except HTTPException as e:
        print(e)
        response.message = e.detail
        return generic_error_response(response, e.status_code)
    except Exception as e:
        print(e)
        return internal_server_error_response(response)


@router.get(
    "/search/locations",
    response_model=ResponseSchema[List[LotRelevantLocation]],
)
def search_lots_relevant_locations(
    q: str, limit: int = 5, db: Session = Depends(get_db_properties)
):
    response = ResponseSchema(status="error", message="Error getting lot")

    cache_key = f"lots:search:locations:{q}:{limit}"
    cached_data = check_cache(cache_key)

    if cached_data:
        return success_response(cached_data)

    try:
        data = search_lots_relevant_locations_service.execute(db, q, limit)

        response.data = [
            LotRelevantLocation(**loc).dict(by_alias=True)
            for loc in data["locations"]
        ]
        response.status = "success"
        response.message = "success"

        set_cache(cache_key, response.dict())

        return success_response(response)
    except HTTPException as e:
        print(e)
        response.message = e.detail
        return generic_error_response(response, e.status_code)
    except Exception as e:
        print(e)
        return internal_server_error_response(response)


@router.get("/", response_model=ResponseSchema[List[LotHomePage]])
def get_lots(
    params: LotsQueryParams = Depends(),
    db: Session = Depends(get_db_properties),
):
    response = ResponseSchema(status="error", message="Error fetching lots")
    params_dict = params.dict(exclude_unset=True)
    # cache_key = (
    #     f"properties:{json.dumps(sorted(params_dict.items()), sort_keys=True)}"
    # )

    # if checked_cache := check_cache(cache_key):
    #     return success_response(checked_cache)

    try:
        data = get_lot_list_service.execute(db=db, params=params_dict)

        response.data = [LotHomePage(**lot) for lot in data["lot_list"]]
        response.status = "success"
        response.message = "Success"
        response.meta = data["meta"]

        # set_cache(cache_key, response.dict())

        return success_response(response)
    except HTTPException as e:
        print(e)
        response.message = e.detail
        return generic_error_response(response, e.status_code)
    except Exception as e:
        print(e)
        return internal_server_error_response(response)


@router.get("/points/", response_model=ResponseSchema[LotPoints])
def read_lot_points(
    lat: float,
    lon: float,
    area: float,
    spacing: int,
    distance: int,
):
    response = ResponseSchema(
        status="error", message="Error getting lot points"
    )
    try:
        # Get the lot points from the service
        lot_points_data = get_lot_points_service.execute(
            lat=lat,
            lon=lon,
            area=area,
            spacing=spacing,
            distance=distance,
        )
        # print(lot_points_data)
        # Map the list of lists to GeograficalPoint instances
        points = [
            GeograficalPoint(lat=float(point[0]), lon=float(point[1]))
            for point in lot_points_data
        ]

        # Create a LotPoints instance
        lot_points = LotPoints(points=points)

        response.status = "success"
        response.message = "Success"
        response.data = lot_points

        return success_response(response)

    except HTTPException as e:
        print(e)
        response.message = e.detail
        return generic_error_response(response, e.status_code)
    except Exception as e:
        print(e)
        return internal_server_error_response(response)


@router.get("/volume/", response_model=ResponseSchema[LotVolume])
def read_lot_volume(
    polygon_points: str = Query(...),
    num_points: int = 400,
):
    response = ResponseSchema(
        status="error", message="Error getting lot volume"
    )
    try:

        # Call the service to get the lot volume
        elevation_data, elevation_difference = get_lot_volume_service.execute(
            polygon_points=polygon_points,
            num_points=num_points,
        )

        # Create a LotVolume instance
        lot_volume = LotVolume(
            points=[
                GeograficalPointElevation(lat=lat, lon=lon, elevation=elev)
                for lat, lon, elev in elevation_data
            ],
            elevation_difference=elevation_difference,
        )

        response.status = "success"
        response.message = "Success"
        response.data = lot_volume

        return success_response(response)

    except HTTPException as e:
        print(e)
        response.message = e.detail
        return generic_error_response(response, e.status_code)
    except Exception as e:
        print(e)
        return internal_server_error_response(response)


@router.get(
    "/filters/histogram", response_model=ResponseSchema[LotHistogramMatrix]
)
def get_lot_histogram(
    params: LotHistogramMatrixParams = Depends(),
    db: Session = Depends(get_db_properties),
):

    response = ResponseSchema(
        status="error", message="Error getting lots histogram"
    )
    try:
        lot_histogram = get_lots_histogram_service.execute(params, db)

        response.status = "success"
        response.message = "Success"
        response.data = LotHistogramMatrix(**lot_histogram)

        return success_response(response)
    except HTTPException as e:
        print(e)
        response.message = e.detail
        return generic_error_response(response, e.status_code)
    except Exception as e:
        print(e)
        return internal_server_error_response(response)


@router.get("/{lot_id}/routes", response_model=LotRoutesResponse)
def get_route(
    lot_id: int,
    params: LotRouteParams = Depends(),
    db: Session = Depends(get_db_properties),
):
    try:
        return get_lot_routes_service.execute(lot_id, params, db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
