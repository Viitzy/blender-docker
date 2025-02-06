from psycopg2.extensions import connection as Connection

from account.src.crud.properties_tables.company_contacts import (
    get_company_contacts,
)


def execute(db: Connection, company_id: int):
    contacts = get_company_contacts(db, company_id)
    if not contacts:
        return {"company_contacts": []}

    return {
        "company_contacts": [
            {
                "id": contact["company_contact_id"],
                "value": contact["contact_value"],
                "type": {
                    "id": contact["contact_type_id"],
                    "name": contact["contact_type_name"],
                },
                "created_at": contact["created_at"],
                "updated_at": contact["updated_at"],
            }
            for contact in contacts
        ]
    }
