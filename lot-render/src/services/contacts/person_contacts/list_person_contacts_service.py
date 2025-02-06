from psycopg2.extensions import connection as Connection
from account.src.crud.global_tables.person_contacts import list_person_contacts
from account.src.services.users import get_user_generic_fields_service
from account.src.utils import mask_contact_value


def execute(db: Connection, user_id: int, masked: bool = True):
    user = get_user_generic_fields_service.execute(db, user_id, ["person_id"])
    person_contacts = list_person_contacts(db, user["person_id"])

    return {
        "person_contacts": [
            {
                "id": person_contact["person_contact_id"],
                "value": (
                    mask_contact_value(person_contact["contact_value"])
                    if masked
                    else person_contact["value"]
                ),
                "is_primary": person_contact["ind_primary_contact"],
                "type": {
                    "id": person_contact["contact_type_id"],
                    "name": person_contact["contact_type_name"],
                },
                "created_at": person_contact["person_contact_created_at"],
                "updated_at": person_contact["person_contact_updated_at"],
            }
            for person_contact in person_contacts
        ]
    }
