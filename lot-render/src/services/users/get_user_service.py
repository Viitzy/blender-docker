from account.src.crud.authentication_tables.users import get_user
from account.src.crud.global_tables.person_contacts import list_person_contacts
from account.src.crud.authentication_tables.user_roles import list_user_roles
from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection


def execute(db: Connection, user_id: int, complete: bool = False):
    try:
        user = get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user_data = {
            "user_id": user["user_id"],
            "username": user["username"],
            "login_type": (
                user["external_provider_name"].lower()
                if user.get("external_provider_name")
                else "email" if "@" in user["username"] else "phone"
            ),
            "person": {
                "id": user["person_id"],
                "name": user["person_name"],
                "preferred_name": user["preferred_name"],
                "identification": user["identification"],
                "birth_date": user["birth_date"],
                "profile_picture": user["profile_picture"],
                "contacts": [],
                "created_at": user["person_created_at"],
                "updated_at": user["person_updated_at"],
            },
            "status": {
                "id": user["userstatus_id"],
                "name": user["userstatus_name"],
            },
            "language": {
                "id": user["language_id"],
                "name": user["language_name"],
            },
            "currency": {
                "id": user["currency_id"],
                "name": user["currency_name"],
            },
            "timezone": {
                "id": user["timezone_id"],
                "name": user["timezone_name"],
            },
            "email_confirmed": user["email_confirmed"],
            "phone_confirmed": user["phone_confirmed"],
            "created_at": user["user_created_at"],
            "updated_at": user["user_updated_at"],
        }

        if user.get("gender_id"):
            user_data["person"]["gender"] = {
                "id": user["gender_id"],
                "name": user["gender_name"],
            }

        contacts = list_person_contacts(db, user["person_id"])
        if contacts:
            user_data["person"]["contacts"] = [
                {
                    "id": contact["person_contact_id"],
                    "value": contact["contact_value"],
                    "is_primary": contact["ind_primary_contact"],
                    "type": {
                        "id": contact["contact_type_id"],
                        "name": contact["contact_type_name"],
                    },
                    "created_at": contact["created_at"],
                    "updated_at": contact["updated_at"],
                }
                for contact in contacts
            ]

        user_roles = list_user_roles(db, user_id)
        if user_roles:
            user_data["roles"] = [
                {"id": role["role_id"], "name": role["role_name"]}
                for role in user_roles
            ]

        if complete:
            user_data["password_hash"] = user["password_hash"]
            user_data["salt"] = user["salt"]

        return user_data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
