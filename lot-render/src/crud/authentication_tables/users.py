from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor
from shared.utils.mount_sql import mount_update_query


def generic_get_user(db: Connection, user_id: int, columns: list):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        f"""SELECT {', '.join(columns)}
        FROM authentication.users 
        WHERE user_id = %(user_id)s""",
        {"user_id": user_id},
    )
    resp = cursor.fetchone()
    cursor.close()
    return resp


def get_user(db: Connection, user_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT u.*, p.*, us.*, l.*, c.*, t.*, g.*, ep.external_provider_name,
            u.created_at AS user_created_at, 
            u.updated_at AS user_updated_at, 
            p.created_at AS person_created_at, 
            p.updated_at AS person_updated_at, 
            us.created_at AS status_created_at, 
            us.updated_at AS status_updated_at, 
            l.created_at AS language_created_at, 
            l.updated_at AS language_updated_at, 
            c.created_at AS currency_created_at, 
            c.updated_at AS currency_updated_at, 
            t.created_at AS timezone_created_at, 
            t.updated_at AS timezone_updated_at, 
            g.created_at AS gender_created_at, 
            g.updated_at AS gender_updated_at 
        FROM authentication.users u
        JOIN global.people p ON u.person_id = p.person_id
        JOIN authentication.userstatus us ON u.userstatus_id = us.userstatus_id
        JOIN global.language l ON u.language_id = l.language_id
        JOIN global.currency c ON u.currency_id = c.currency_id
        JOIN global.timezone t ON u.timezone_id = t.timezone_id
        LEFT JOIN global.gender g ON p.gender_id = g.gender_id
        LEFT JOIN authentication.user_external_providers uxp ON u.user_id = uxp.user_id
        LEFT JOIN authentication.external_providers ep ON uxp.external_provider_id = ep.external_provider_id
        WHERE u.user_id = %(user_id)s
        """,
        {"user_id": user_id},
    )
    user = cursor.fetchone()
    cursor.close()
    return user


def update_user(db: Connection, user_id: int, data: dict):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            f"""
        UPDATE authentication.users SET {mount_update_query(data)}
        WHERE user_id = %(user_id)s RETURNING user_id
        """,
            {"user_id": user_id, **data},
        )
        user_id = cursor.fetchone()["user_id"]
        db.commit()
        cursor.close()
        return user_id
    except Exception as e:
        db.rollback()
        cursor.close()
        return None


def get_user_by_username(db: Connection, username: str) -> dict:
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT u.*, ur.role_id FROM authentication.users u
        JOIN authentication.user_roles ur ON u.user_id = ur.user_id
        WHERE u.username = %(username)s
        """,
        {"username": username},
    )
    return cursor.fetchone()
