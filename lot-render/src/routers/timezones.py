from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from account.src.services.timezones import (
    get_timezone_service,
    list_timezones_service,
)
from shared.database.db_session import get_db_account
from account.src.schemas.timezones_schemas import (
    TimezoneResponse,
    TimezoneListResponse,
)

router = APIRouter(tags=["timezones"])


@router.get("/{timezone_id}", response_model=TimezoneResponse)
def get_timezone_route(timezone_id: int, db: Session = Depends(get_db_account)):
    try:
        return get_timezone_service.execute(db, timezone_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting timezone",
        )


@router.get("/", response_model=TimezoneListResponse)
def list_timezones_route(db: Session = Depends(get_db_account)):
    try:
        return list_timezones_service.execute(db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing timezones",
        )
