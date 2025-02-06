from psycopg2.extensions import connection as Connection
from account.src.crud.authentication_tables.sessions import (
    delete_all_sessions,
)


def execute(db: Connection, user_id: int):
    session_ids = delete_all_sessions(db, user_id)
    return session_ids
