from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from account.src.schemas.currencies_schemas import (
    CurrencyResponse,
    CurrenciesListResponse,
)
from account.src.services.currencies import (
    get_currency_service,
    list_currencies_service,
)
from shared.database.db_session import get_db_account


router = APIRouter(tags=["currencies"])


@router.get("/{currency_id}", response_model=CurrencyResponse)
def get_currency_route(currency_id: int, db: Session = Depends(get_db_account)):
    try:
        return get_currency_service.execute(db, currency_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e
        )


@router.get("/", response_model=CurrenciesListResponse)
def list_currencies_route(db: Session = Depends(get_db_account)):
    try:
        return list_currencies_service.execute(db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e,
        )
