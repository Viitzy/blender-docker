from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_contact_type(db: Connection, contact_type_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT 
            contact_type_id AS id, 
            contact_type_name AS name 
        FROM global.contact_types
        WHERE contact_type_id = %(contact_type_id)s""",
        {"contact_type_id": contact_type_id},
    )
    return cursor.fetchone()


def list_contact_types(db: Connection):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT  contact_type_id AS id, 
            contact_type_name AS name 
        FROM global.contact_types"""
    )
    return cursor.fetchall()


def get_contact_type_by_type(db: Connection, contact_type: str):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT contact_type_id AS id FROM global.contact_types
        WHERE lower(contact_type_name) = lower(%(contact_type)s)""",
        {"contact_type": contact_type},
    )
    return cursor.fetchone()
