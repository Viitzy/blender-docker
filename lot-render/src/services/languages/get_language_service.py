from account.src.crud.global_tables.languages import get_language
from psycopg2.extensions import connection as Connection
from fastapi import HTTPException, status


def execute(db: Connection, language_id: int):
    language = get_language(db, language_id)
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Language not found"
        )

    return {"id": language["language_id"], "name": language["language_name"]}
