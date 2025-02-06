from psycopg2.extensions import connection as Connection
from account.src.crud.authentication_tables.users import generic_get_user
from fastapi import HTTPException, status


def execute(db: Connection, user_id: int, columns: list[str]):
    user = generic_get_user(db, user_id, columns)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
