from datetime import datetime
from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor


def get_person_contact(db: Connection, contact_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT *, 
            pc.created_at AS person_contact_created_at, 
            pc.updated_at AS person_contact_updated_at, 
            ct.created_at AS contact_type_created_at, 
            ct.updated_at AS contact_type_updated_at
        FROM global.person_contacts pc
        JOIN global.contact_types ct ON pc.contact_type_id = ct.contact_type_id
        WHERE pc.person_contact_id = %(contact_id)s""",
        {"contact_id": contact_id},
    )
    return cursor.fetchone()


def list_person_contacts(db: Connection, person_id: int):
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """SELECT *,
                pc.created_at AS person_contact_created_at, 
                pc.updated_at AS person_contact_updated_at, 
                ct.created_at AS contact_type_created_at, 
                ct.updated_at AS contact_type_updated_at
            FROM global.person_contacts pc
            JOIN global.contact_types ct ON pc.contact_type_id = ct.contact_type_id
            WHERE pc.person_id = %(person_id)s""",
            {"person_id": person_id},
        )
        return cursor.fetchall()
    except Exception as e:
        print(e)


def create_person_contact(db: Connection, data: dict):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """INSERT INTO global.person_contacts (
            person_id, 
            contact_type_id, 
            contact_value,
            created_at,
            updated_at,
            ind_primary_contact
        ) 
        VALUES (
            %(person_id)s, 
            %(contact_type_id)s, 
            %(contact_value)s,
            %(created_at)s,
            %(updated_at)s,
            %(ind_primary_contact)s
        ) 
        RETURNING person_contact_id""",
        {
            "person_id": data["person_id"],
            "contact_type_id": data["contact_type_id"],
            "contact_value": data["contact_value"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "ind_primary_contact": data.get("ind_primary_contact", False),
        },
    )
    db.commit()
    return cursor.fetchone()


def delete_person_contact(db: Connection, contact_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """DELETE FROM global.person_contacts 
        WHERE person_contact_id = %(contact_id)s
        RETURNING person_contact_id""",
        {"contact_id": contact_id},
    )
    db.commit()
    return cursor.fetchone()


def update_person_contact(db: Connection, contact_id: int, new_contact: str):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """UPDATE global.person_contacts 
        SET contact_value = %(new_contact)s 
        WHERE person_contact_id = %(contact_id)s 
        RETURNING person_contact_id""",
        {"contact_id": contact_id, "new_contact": new_contact},
    )
    db.commit()
    return cursor.fetchone()
