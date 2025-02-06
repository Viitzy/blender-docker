from psycopg2.extensions import connection as Connection
from account.src.crud.authentication_tables.verification_tokens import (
    delete_verification_token,
)


def execute(db: Connection, user_id: int, token: str, token_type: str):
    delete_verification_token(db, user_id, token, token_type)
    return {"message": "Token deleted successfully"}
