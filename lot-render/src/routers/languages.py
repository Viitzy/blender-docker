from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.languages import get_language_service, list_languages_service
from schemas.languages_schemas import LanguageResponse, LanguagesListResponse
from shared.database.db_session import get_db_account


router = APIRouter(tags=["languages"])


@router.get("/{language_id}", response_model=LanguageResponse)
def get_language_route(language_id: int, db: Session = Depends(get_db_account)):
    try:
        return get_language_service.execute(db, language_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting language",
        )


@router.get("/", response_model=LanguagesListResponse)
def list_languages_route(db: Session = Depends(get_db_account)):
    try:
        return list_languages_service.execute(db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing languages",
        )
