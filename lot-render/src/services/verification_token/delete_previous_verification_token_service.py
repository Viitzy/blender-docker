from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection

from account.src.crud.authentication_tables.verification_tokens import (
    delete_previous_verification_token,
)


def execute(db: Connection, user_id: int, token_type: str):
    delete_previous_verification_token(db, user_id, token_type)
    return {"message": "Token deleted successfully"}
