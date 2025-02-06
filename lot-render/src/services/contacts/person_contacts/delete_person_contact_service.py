from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection
from account.src.crud.global_tables.person_contacts import delete_person_contact
from account.src.services.users import get_user_generic_fields_service
from account.src.services.contacts.person_contacts import (
    get_person_contact_service,
)


def execute(db: Connection, user_id: int, contact_id: int):
    user = get_user_generic_fields_service.execute(db, user_id, ["person_id"])
    person_contact = get_person_contact_service.execute(db, user_id, contact_id)
    if person_contact["person_id"] != user["person_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this contact",
        )

    deleted_id = delete_person_contact(db, contact_id)
    if not deleted_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    return {"message": "Contact deleted successfully"}
