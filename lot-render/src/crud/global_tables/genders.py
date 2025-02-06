from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_gender(db: Connection, gender_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM global.gender WHERE gender_id = %(gender_id)s",
        {"gender_id": gender_id},
    )
    return cursor.fetchone()


def list_genders(db: Connection):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM global.gender")
    return cursor.fetchall()
