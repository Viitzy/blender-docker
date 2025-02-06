from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection
from account.src.crud.global_tables.contact_types import get_contact_type


def execute(db: Connection, contact_type_id: int):
    contact_type = get_contact_type(db, contact_type_id)
    if not contact_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact type not found",
        )
    return contact_type
