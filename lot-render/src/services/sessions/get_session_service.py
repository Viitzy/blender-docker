from psycopg2.extensions import connection as Connection
from account.src.crud.authentication_tables.sessions import get_session


def execute(db: Connection, session_id: str):
    return get_session(db, session_id)
