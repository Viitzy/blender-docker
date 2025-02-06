from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection
from account.src.crud.global_tables.currencies import get_currency


def execute(db: Connection, currency_id: int):
    currency = get_currency(db, currency_id)
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Currency not found"
        )
    return {"id": currency["currency_id"], "name": currency["currency_name"]}
