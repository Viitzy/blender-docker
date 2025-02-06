from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_currency(db: Connection, currency_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM global.currency WHERE currency_id = %(currency_id)s",
        {"currency_id": currency_id},
    )
    return cursor.fetchone()


def list_currencies(db: Connection):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM global.currency")
    return cursor.fetchall()
