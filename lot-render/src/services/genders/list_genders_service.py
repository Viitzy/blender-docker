from psycopg2.extensions import connection as Connection
from account.src.crud.global_tables.genders import list_genders


def execute(db: Connection):
    genders = list_genders(db)
    return {
        "genders": [
            {"id": gender["gender_id"], "name": gender["gender_name"]}
            for gender in genders
        ]
    }
