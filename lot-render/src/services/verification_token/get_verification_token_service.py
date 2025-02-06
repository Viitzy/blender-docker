from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection

from account.src.crud.authentication_tables.verification_tokens import (
    get_verification_token,
)


def execute(db: Connection, user_id: int, token: str, token_type: str):
    token_data = get_verification_token(db, user_id, token, token_type)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token not found"
        )
    return token_data
