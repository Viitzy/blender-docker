from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection
from account.src.crud.global_tables.person_contacts import get_person_contact
from account.src.services.users import get_user_generic_fields_service


def execute(db: Connection, user_id: int, contact_id: int):
    user = get_user_generic_fields_service.execute(db, user_id, ["person_id"])

    person_contact = get_person_contact(db, contact_id)
    if not person_contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    if person_contact["person_id"] != user["person_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this contact",
        )

    person_contact_data = {
        "id": person_contact["person_contact_id"],
        "value": person_contact["contact_value"],
        "is_primary": person_contact["ind_primary_contact"],
        "type": {
            "id": person_contact["contact_type_id"],
            "name": person_contact["contact_type_name"],
        },
        "created_at": person_contact["person_contact_created_at"],
        "updated_at": person_contact["person_contact_updated_at"],
    }

    return person_contact_data
