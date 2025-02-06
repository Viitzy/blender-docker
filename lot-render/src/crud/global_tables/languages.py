from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_language(db: Connection, language_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM global.language WHERE language_id = %(language_id)s",
        {"language_id": language_id},
    )
    return cursor.fetchone()


def list_languages(db: Connection):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM global.language")
    return cursor.fetchall()
