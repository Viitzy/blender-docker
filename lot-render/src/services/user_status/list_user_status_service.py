from psycopg2.extensions import connection as Connection
from account.src.crud.authentication_tables.user_status import list_user_status


def execute(db: Connection):
    user_statuses = list_user_status(db)
    return {"user_statuses": user_statuses}
