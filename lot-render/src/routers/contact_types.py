from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from account.src.services.contact_types import get_contact_type_service
from account.src.services.contact_types import list_contact_types_service
from account.src.schemas.contact_types_schemas import (
    ContactTypeResponse,
    ContactTypeListResponse,
)
from shared.database.db_session import get_db_account


router = APIRouter(tags=["contact_types"])


@router.get("/{contact_type_id}", response_model=ContactTypeResponse)
def get_contact_type_route(
    contact_type_id: int, db: Session = Depends(get_db_account)
):
    try:
        return get_contact_type_service.execute(db, contact_type_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e
        )


@router.get("/", response_model=ContactTypeListResponse)
def list_contact_types_route(db: Session = Depends(get_db_account)):
    try:
        return list_contact_types_service.execute(db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e,
        )
