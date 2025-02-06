from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_company_contacts(db: Connection, company_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT *
        FROM properties.company_contacts cc
        JOIN global.contact_types ct ON cc.contact_type_id = ct.contact_type_id
        WHERE cc.company_id = %(company_id)s
        """,
        {"company_id": company_id},
    )
    return cursor.fetchall()


def list_company_contacts(db: Connection, company_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT *
        FROM properties.company_contacts cc
        JOIN global.contact_types ct ON cc.contact_type_id = ct.contact_type_id
        WHERE cc.company_id = %(company_id)s
        """,
        {"company_id": company_id},
    )
    return cursor.fetchall()


def create_company_contact(db: Connection, data: dict):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        INSERT INTO properties.company_contacts (
            company_id, 
            contact_type_id, 
            contact_value,
            created_at,
            updated_at
        )
        VALUES (
            %(company_id)s, 
            %(contact_type_id)s, 
            %(contact_value)s, 
            now(), 
            now()
        )
        RETURNING company_contact_id
        """,
        data,
    )
    company_contact_id = cursor.fetchone()["company_contact_id"]
    db.commit()
    cursor.close()
    return company_contact_id


def update_company_contact(
    db: Connection, company_contact_id: int, contact_value: str
):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        UPDATE properties.company_contacts
        SET contact_value = %(contact_value)s, updated_at = now()
        WHERE company_contact_id = %(company_contact_id)s
        RETURNING company_contact_id
        """,
        {
            "company_contact_id": company_contact_id,
            "contact_value": contact_value,
        },
    )
    company_contact_id = cursor.fetchone()["company_contact_id"]
    db.commit()
    cursor.close()
    return company_contact_id


def search_company_contact(db: Connection, contact_value: str):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT * FROM properties.company_contacts WHERE contact_value = %(contact_value)s
        """,
        {"contact_value": contact_value},
    )
    return cursor.fetchone()
