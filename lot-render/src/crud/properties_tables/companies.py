from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor
from shared.utils.mount_sql import mount_update_query


def get_company(db: Connection, company_id: int):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT *, c.created_at AS company_created_at, c.updated_at AS company_updated_at 
        FROM properties.companies c
        JOIN properties.company_types ct ON c.company_type_id = ct.company_type_id
        LEFT JOIN global.addresses a ON c.address_id = a.address_id
		LEFT JOIN global.street s ON s.street_id = a.street_id
		LEFT JOIN global.neighborhoods n ON n.neighborhood_id = a.neighborhood_id
        LEFT JOIN global.cities ci ON n.city_id = ci.city_id
        LEFT JOIN global.states st ON ci.state_id = st.state_id
        LEFT JOIN global.countries co ON st.country_id = co.country_id
        WHERE c.company_id = %(company_id)s
        """,
        {"company_id": company_id},
    )
    return cursor.fetchone()


def update_company(db: Connection, company_id: int, data: dict):
    cursor = db.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute(
            f"""
        UPDATE properties.companies SET {mount_update_query(data)}
        WHERE company_id = %(company_id)s
        RETURNING company_id
        """,
            {"company_id": company_id, **data},
        )
        company_id = cursor.fetchone()["company_id"]
        db.commit()
        cursor.close()
        return company_id
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e
