from fastapi import HTTPException
from psycopg2.extensions import connection as Connection
from account.src.crud.authentication_tables.user_status import get_user_status


def execute(db: Connection, user_status_id: int):
    user_status = get_user_status(db, user_status_id)
    if not user_status:
        raise HTTPException(status_code=404, detail="User status not found")
    return user_status
