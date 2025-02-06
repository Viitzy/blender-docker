from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_role(db: Connection, role_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM authentication.roles WHERE role_id = %(role_id)s",
        {"role_id": role_id},
    )
    return cursor.fetchone()


def list_roles(db: Connection):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM authentication.roles")
    return cursor.fetchall()
