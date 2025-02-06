from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from account.src.services.users import (
    check_user_exists_service,
    get_user_service,
    update_user_password_service,
    update_user_service,
    create_user_report_service,
    delete_user_service,
)
from shared.utils.jwt_decoder import get_jwt_payload
from account.src.schemas.users_schemas import (
    UserUpdate,
    UserPasswordUpdate,
    UserReportCreate,
    UserResponse,
    UserExistsResponse,
    UserReportResponse,
    UserUpdateResponse,
    UserDeleteResponse,
)
from shared.database.db_session import get_db_account

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_user_route(
    db: Session = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
):
    try:
        return get_user_service.execute(db, jwt_data["sub"])
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting user",
        )


@router.patch("/me", response_model=UserUpdateResponse)
def update_user_route(
    data: UserUpdate,
    db: Session = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
):
    try:
        data = data.model_dump(exclude_unset=True)
        return update_user_service.execute(db, jwt_data["sub"], data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user",
        )


@router.patch("/me/password", response_model=UserUpdateResponse)
def update_user_password_route(
    data: UserPasswordUpdate,
    db: Session = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
    x_session_id: str = Header(default=None),
):
    try:
        return update_user_password_service.execute(
            db, jwt_data["sub"], x_session_id, data
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user password",
        )


@router.post("/me/report", response_model=UserReportResponse)
def create_my_user_report_route(
    data: UserReportCreate,
    db: Session = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
):
    try:
        return create_user_report_service.execute(db, jwt_data["sub"], data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user report",
        )


@router.get("/exists", response_model=UserExistsResponse)
def check_user_exists(
    username: str,
    db: Session = Depends(get_db_account),
):
    try:
        return check_user_exists_service.execute(db, username)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking user exists",
        )


@router.delete("/me", response_model=UserDeleteResponse)
def delete_user_route(
    db: Session = Depends(get_db_account),
    jwt_data: dict = Depends(get_jwt_payload),
):
    try:
        return delete_user_service.execute(db, jwt_data["sub"])
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting user",
        )
