from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_user_status(db: Connection, user_status_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT 
            userstatus_id AS id, 
            userstatus_name AS name 
        FROM authentication.userstatus 
        WHERE userstatus_id = %(user_status_id)s""",
        {"user_status_id": user_status_id},
    )
    return cursor.fetchone()


def list_user_status(db: Connection):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT 
            userstatus_id AS id, 
            userstatus_name AS name 
        FROM authentication.userstatus"""
    )
    return cursor.fetchall()
