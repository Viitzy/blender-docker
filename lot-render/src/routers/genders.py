from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.genders import get_gender_service, list_genders_service
from schemas.genders_schemas import GenderResponse, GendersListResponse
from shared.database.db_session import get_db_account


router = APIRouter(tags=["genders"])


@router.get("/{gender_id}", response_model=GenderResponse)
def get_gender_route(gender_id: int, db: Session = Depends(get_db_account)):
    try:
        return get_gender_service.execute(db, gender_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting gender",
        )


@router.get("/", response_model=GendersListResponse)
def list_genders_route(db: Session = Depends(get_db_account)):
    try:
        return list_genders_service.execute(db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing genders",
        )
