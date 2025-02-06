from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection
import random
from account.src.crud.authentication_tables.users import update_user
from account.src.crud.global_tables.people import update_person
from account.src.crud.global_tables.person_contacts import update_person_contact
from account.src.services.sessions import delete_all_sessions_service
from account.src.services.users import get_user_service
from shared.utils.constants import USER_STATUS_DELETED


def execute(db: Connection, user_id: int):
    user = get_user_service.execute(db, user_id)

    username = user["username"]
    person = user["person"]
    contacts = person["contacts"]

    for contact in contacts:
        update_person_contact(
            db,
            contact["id"],
            "".join(random.sample(contact["value"], len(contact["value"]))),
        )

    update_person(
        db,
        person["id"],
        {
            "person_name": (
                "".join(random.sample(person["name"], len(person["name"])))
                if person["name"]
                else None
            ),
            "preferred_name": (
                "".join(
                    random.sample(
                        person["preferred_name"], len(person["preferred_name"])
                    )
                )
                if person["preferred_name"]
                else None
            ),
        },
    )

    update_user(
        db,
        user_id,
        {
            "username": f"{''.join(random.sample(username, len(username)))}#deleted",
            "userstatus_id": USER_STATUS_DELETED,
        },
    )

    delete_all_sessions_service.execute(db, user_id)

    return {"message": "User deleted successfully"}
