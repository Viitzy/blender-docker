from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor
from account.src.schemas.people_schemas import PersonUpdate
from shared.utils.mount_sql import mount_update_query


def update_person(db: Connection, person_id: int, data: dict):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            f"""
            UPDATE global.people SET {mount_update_query(data)}
            WHERE person_id = %(person_id)s RETURNING person_id
            """,
            {"person_id": person_id, **data},
        )
        person_id = cursor.fetchone()["person_id"]
        db.commit()
        cursor.close()
        return person_id
    except Exception as e:
        db.rollback()
        cursor.close()
        return None
