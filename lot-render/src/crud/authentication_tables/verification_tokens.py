from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_verification_token(
    db: Connection, user_id: int, token: str, token_type: str
):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT * FROM authentication.verification_tokens 
        WHERE user_id = %(user_id)s 
        AND token = %(token)s 
        AND type = %(type)s""",
        {"user_id": user_id, "token": token, "type": token_type},
    )
    return cursor.fetchone()


def delete_verification_token(
    db: Connection, user_id: int, token: str, token_type: str
):
    cursor = db.cursor()
    cursor.execute(
        """DELETE FROM authentication.verification_tokens 
        WHERE user_id = %(user_id)s 
        AND token = %(token)s 
        AND type = %(type)s
        RETURNING token_id""",
        {"user_id": user_id, "token": token, "type": token_type},
    )
    token_id = cursor.fetchone()["token_id"]
    db.commit()
    return token_id


def delete_previous_verification_token(
    db: Connection, user_id: int, token_type: str
):
    cursor = db.cursor()
    cursor.execute(
        """DELETE FROM authentication.verification_tokens 
        WHERE user_id = %(user_id)s 
        AND type = %(type)s
        RETURNING token_id""",
        {"user_id": user_id, "type": token_type},
    )
    token_id = cursor.fetchone()["token_id"]
    db.commit()
    return token_id
