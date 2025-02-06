from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection as Connection
from account.src.schemas.person_contacts_schemas import (
    PersonContactListResponse,
    PersonContactResponse,
    PersonContactDeleteResponse,
    PersonContactUpdate,
    PersonContactUpdateResponse,
)
from shared.database.db_session import get_db_account
from shared.utils.jwt_decoder import get_jwt_payload
from account.src.services.contacts.person_contacts import (
    delete_person_contact_service,
    get_person_contact_service,
    list_person_contacts_service,
)
from account.src.services.contacts import update_contact_service

router = APIRouter(tags=["contacts"])


@router.get("/person", response_model=PersonContactListResponse)
def list_person_contacts_route(
    db: Connection = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
):
    try:
        return list_person_contacts_service.execute(db, jwt_data["sub"])
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e,
        )


@router.get("/{contact_id}/person", response_model=PersonContactResponse)
def get_person_contact_route(
    contact_id: int,
    db: Connection = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
):
    try:
        return get_person_contact_service.execute(
            db, jwt_data["sub"], contact_id
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{contact_id}/person", response_model=PersonContactDeleteResponse
)
def delete_person_contact_route(
    contact_id: int,
    db: Connection = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
):
    try:
        return delete_person_contact_service.execute(
            db, jwt_data["sub"], contact_id
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/", response_model=PersonContactUpdateResponse)
def post_contact_route(
    contact_data: PersonContactUpdate,
    jwt_data: dict = Depends(get_jwt_payload),
    db: Connection = Depends(get_db_account),
):
    try:
        return update_contact_service.execute(
            db, jwt_data["sub"], jwt_data["permission"], contact_data
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred. Please try again later.",
        )
