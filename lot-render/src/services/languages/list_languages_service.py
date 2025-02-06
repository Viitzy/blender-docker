from account.src.crud.global_tables.languages import list_languages
from psycopg2.extensions import connection as Connection
from fastapi import HTTPException, status


def execute(db: Connection):
    languages = list_languages(db)
    return {
        "languages": [
            {"id": language["language_id"], "name": language["language_name"]}
            for language in languages
        ]
    }
