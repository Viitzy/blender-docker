from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_timezone(db: Connection, timezone_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM global.timezone WHERE timezone_id = %(timezone_id)s",
        {"timezone_id": timezone_id},
    )
    return cursor.fetchone()


def list_timezones(db: Connection):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM global.timezone")
    return cursor.fetchall()
