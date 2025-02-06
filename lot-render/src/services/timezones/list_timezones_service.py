from account.src.crud.global_tables.timezones import list_timezones
from psycopg2.extensions import connection as Connection


def execute(db: Connection):
    timezones = list_timezones(db)
    return {
        "timezones": [
            {"id": timezone["timezone_id"], "name": timezone["timezone_name"]}
            for timezone in timezones
        ]
    }
