from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection
from account.src.crud.properties_tables.company_users import (
    get_company_by_user_id,
)


def execute(db: Connection, user_id: int):
    company = get_company_by_user_id(db, user_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return company
