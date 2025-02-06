from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extensions import connection as Connection
from account.src.services.companies import (
    get_company_service,
    update_company_service,
    delete_company_service,
)
from account.src.schemas.companies_schemas import (
    CompanyResponse,
    CompanyUpdate,
    CompanyUpdateResponse,
)
from shared.database.db_session import get_db_account
from shared.utils.jwt_decoder import get_jwt_payload
from shared.utils.constants import PERMISSION_ID_REAL_ESTATE

router = APIRouter(tags=["companies"])


@router.get("/", response_model=CompanyResponse)
def get_company(
    db: Connection = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
):
    try:
        if jwt_data["permission"] != PERMISSION_ID_REAL_ESTATE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed",
            )

        return get_company_service.execute(db, jwt_data["sub"])
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch("/", response_model=CompanyUpdateResponse)
def update_company(
    data: CompanyUpdate,
    db: Connection = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
):
    try:
        if jwt_data["permission"] != PERMISSION_ID_REAL_ESTATE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed",
            )

        data = data.model_dump(exclude_unset=True)
        return update_company_service.execute(db, jwt_data["sub"], data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/")
def delete_company(
    db: Connection = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
):
    try:
        if jwt_data["permission"] != PERMISSION_ID_REAL_ESTATE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed",
            )
        return delete_company_service.execute(db, jwt_data["sub"])
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
