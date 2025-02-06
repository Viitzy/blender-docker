from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def list_user_roles(db: Connection, user_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT r.*
        FROM authentication.user_roles ur
        JOIN authentication.roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = %(user_id)s""",
        {"user_id": user_id},
    )
    user_roles = cursor.fetchall()
    cursor.close()

    return user_roles
