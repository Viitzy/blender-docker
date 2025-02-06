from psycopg2.extensions import connection as Connection
from account.src.crud.global_tables.contact_types import (
    get_contact_type_by_type,
)


def execute(db: Connection, contact_type: str):
    return get_contact_type_by_type(db, contact_type)
