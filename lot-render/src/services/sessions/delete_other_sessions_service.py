from psycopg2.extensions import connection as Connection
from account.src.crud.authentication_tables.sessions import (
    delete_other_sessions,
)


def execute(db: Connection, user_id: int, session_id: str):
    session_ids = delete_other_sessions(db, user_id, session_id)
    return session_ids
