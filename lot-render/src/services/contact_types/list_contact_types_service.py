from psycopg2.extensions import connection as Connection
from account.src.crud.global_tables.contact_types import list_contact_types


def execute(db: Connection):
    contact_types = list_contact_types(db)
    return {"contact_types": contact_types}
