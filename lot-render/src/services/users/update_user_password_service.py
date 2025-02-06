from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection
from account.src.crud.authentication_tables.users import update_user
from account.src.services.sessions import (
    get_session_service,
    delete_other_sessions_service,
)
from account.src.services.users import get_user_service
from account.src.schemas.users_schemas import UserPasswordUpdate
from shared.utils.password_hash import hash_password, verify_password
from shared.utils.validators import validate_password


def execute(
    db: Connection, user_id: int, session_id: str, data: UserPasswordUpdate
):
    try:
        session = get_session_service.execute(db, session_id)
        if not session or session["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this password",
            )

        if data.new_password == data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password cannot be the same as the current password",
            )

        if data.new_password != data.confirm_new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password and confirm password do not match",
            )

        password_errors = validate_password(data.new_password)
        if password_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_errors,
            )

        user = get_user_service.execute(db, user_id, complete=True)

        password_match = verify_password(
            data.current_password, user["password_hash"], user["salt"]
        )
        if not password_match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        hashed_password, salt = hash_password(data.new_password)
        data = {
            "password_hash": hashed_password,
            "salt": salt,
        }

        updated_user_id = update_user(db, user_id, data)
        if not updated_user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user password",
            )

        delete_other_sessions_service.execute(db, user_id, session_id)

        return {"message": "User password updated successfully"}
    except HTTPException as e:
        raise e
