from account.src.crud.global_tables.genders import get_gender
from psycopg2.extensions import connection as Connection
from fastapi import HTTPException, status


def execute(db: Connection, gender_id: int):
    gender = get_gender(db, gender_id)
    if not gender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Gender not found"
        )
    return {"id": gender["gender_id"], "name": gender["gender_name"]}
