from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_user_external_provider(db: Connection, user_id: int) -> dict:
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT uep.* FROM authentication.user_external_providers uep
        WHERE uep.user_id = %(user_id)s AND uep.external_provider_id = 1
        """,
        {"user_id": user_id},
    )
    return cursor.fetchone()
