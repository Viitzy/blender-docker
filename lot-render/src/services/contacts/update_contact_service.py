from datetime import datetime
from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection

from account.src.crud.authentication_tables.users import generic_get_user
from account.src.crud.global_tables.person_contacts import update_person_contact
from account.src.crud.properties_tables.company_contacts import (
    update_company_contact,
)
from account.src.crud.properties_tables.company_users import (
    get_company_by_user_id,
)
from account.src.schemas.person_contacts_schemas import PersonContactUpdate
from account.src.services.contact_types import get_contact_type_service
from account.src.services.contacts.person_contacts import (
    create_person_contact_service,
)
from account.src.services.contacts.company_contacts import (
    create_company_contact_service,
)
from account.src.services.users import (
    check_user_exists_service,
    get_user_service,
    update_user_service,
)
from account.src.services.verification_token import (
    delete_previous_verification_token_service,
    get_verification_token_service,
)
from account.src.services.contacts.person_contacts import (
    list_person_contacts_service,
)
from account.src.services.contacts.company_contacts import (
    list_company_contacts_service,
)
from shared.utils.constants import (
    PERMISSION_ID_CUSTOMER,
    PERMISSION_ID_REAL_ESTATE,
)
from shared.utils.formatters import unmask_phone


def execute(
    db: Connection, user_id: int, permission_id: int, data: PersonContactUpdate
):
    if permission_id not in [PERMISSION_ID_CUSTOMER, PERMISSION_ID_REAL_ESTATE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid permission"
        )

    user = get_user_service.execute(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    data.new_contact = (
        data.new_contact.lower().strip()
        if "@" in data.new_contact
        else unmask_phone(data.new_contact).strip()
    )

    if ("@" in user["username"] and "@" in data.new_contact) or (
        "@" not in user["username"] and "@" not in data.new_contact
    ):
        username = check_user_exists_service.execute(db, data.new_contact)
        if username["exists"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            )

    company_id = None
    if permission_id == PERMISSION_ID_REAL_ESTATE:
        company = get_company_by_user_id(db, user_id)
        company_id = company["company_id"]

    contact_type = get_contact_type_service.execute(db, data.contact_type_id)
    token_type = f"change_{contact_type['name'].lower()}"

    token_data = get_verification_token_service.execute(
        db, user_id, data.token, token_type
    )
    if not token_data or token_data["expires_at"] < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )

    delete_previous_verification_token_service.execute(db, user_id, token_type)

    contacts = list_person_contacts_service.execute(db, user_id)[
        "person_contacts"
    ]

    contact_id = None
    for contact in contacts:
        if "@" in contact["value"] and "@" in data.new_contact:
            contact_id = contact["id"]
            break

        if "@" not in contact["value"] and "@" not in data.new_contact:
            contact_id = contact["id"]
            break

    if contact_id:
        update_person_contact(db, contact_id, data.new_contact)
    else:
        create_person_contact_service.execute(
            db,
            {
                "person_id": generic_get_user(db, user_id, ["person_id"])[
                    "person_id"
                ],
                "contact_type_id": contact_type["id"],
                "contact_value": data.new_contact,
            },
        )

    if permission_id == PERMISSION_ID_REAL_ESTATE:
        company_contacts = list_company_contacts_service.execute(
            db, company_id
        )["company_contacts"]

        company_contact_id = None
        for contact in company_contacts:
            if "@" in contact["value"] and "@" in data.new_contact:
                company_contact_id = contact["id"]
                break

            if "@" not in contact["value"] and "@" not in data.new_contact:
                company_contact_id = contact["id"]
                break

        if company_contact_id:
            update_company_contact(db, company_contact_id, data.new_contact)
        else:
            create_company_contact_service.execute(
                db,
                {
                    "company_id": company_id,
                    "contact_type_id": contact_type["id"],
                    "contact_value": data.new_contact,
                },
            )

    if ("@" in data.new_contact and "@" in user["username"]) or (
        "@" not in data.new_contact and "@" not in user["username"]
    ):
        update_user_service.execute(db, user_id, {"username": data.new_contact})

    return {"message": "Contact updated successfully"}
