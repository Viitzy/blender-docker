from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_company_by_user_id(db: Connection, user_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT company_id FROM properties.company_users
        WHERE user_id = %(user_id)s
        AND seller_type_id = %(company_seller_type_id)s
        """,
        {"user_id": user_id, "company_seller_type_id": 1},
    )
    return cursor.fetchone()
