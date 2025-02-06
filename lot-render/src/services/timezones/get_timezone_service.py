from account.src.crud.global_tables.timezones import get_timezone
from psycopg2.extensions import connection as Connection
from fastapi import HTTPException, status


def execute(db: Connection, timezone_id: int):
    timezone = get_timezone(db, timezone_id)
    if not timezone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Timezone not found"
        )
    return {"id": timezone["timezone_id"], "name": timezone["timezone_name"]}
