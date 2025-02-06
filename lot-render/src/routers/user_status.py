from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from account.src.services.user_status import (
    list_user_status_service,
    get_user_status_service,
)
from schemas.user_status_schemas import (
    UserStatusResponse,
    UserStatusListResponse,
)
from shared.database.db_session import get_db_account


router = APIRouter(tags=["user_status"])


@router.get("/{user_status_id}", response_model=UserStatusResponse)
def get_user_status_route(
    user_status_id: int, db: Session = Depends(get_db_account)
):
    try:
        return get_user_status_service.execute(db, user_status_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e
        )


@router.get("/", response_model=UserStatusListResponse)
def list_user_status_route(db: Session = Depends(get_db_account)):
    try:
        return list_user_status_service.execute(db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e,
        )
