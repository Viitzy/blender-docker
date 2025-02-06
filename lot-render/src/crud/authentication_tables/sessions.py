from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_session(db: Connection, session_id: str):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM authentication.sessions WHERE session_id = %(session_id)s",
        {"session_id": session_id},
    )
    session = cursor.fetchone()
    cursor.close()
    return session


def delete_session(db: Connection, session_id: str):
    cursor = db.cursor()
    cursor.execute(
        """DELETE FROM authentication.sessions 
        WHERE session_id = %(session_id)s
        RETURNING session_id""",
        {"session_id": session_id},
    )
    session_id = cursor.fetchone()[0]
    db.commit()
    cursor.close()
    return session_id


def delete_all_sessions(db: Connection, user_id: int):
    cursor = db.cursor()
    cursor.execute(
        """DELETE FROM authentication.sessions 
        WHERE user_id = %(user_id)s
        RETURNING session_id""",
        {"user_id": user_id},
    )
    session_ids = cursor.fetchall()
    db.commit()
    cursor.close()
    return session_ids


def delete_other_sessions(db: Connection, user_id: int, session_id: str):
    cursor = db.cursor()
    cursor.execute(
        """DELETE FROM authentication.sessions 
        WHERE user_id = %(user_id)s AND session_id != %(session_id)s
        RETURNING session_id""",
        {"user_id": user_id, "session_id": session_id},
    )
    session_ids = cursor.fetchall()
    db.commit()
    cursor.close()
    return session_ids
