from account.src.crud.authentication_tables.users import update_user
from account.src.crud.global_tables.people import update_person
from account.src.services.users import get_user_service
from account.src.services.currencies import get_currency_service
from account.src.services.genders import get_gender_service
from account.src.services.languages import get_language_service
from account.src.services.timezones import get_timezone_service
from account.src.schemas.users_schemas import UserUpdate
from psycopg2.extensions import connection as Connection
from fastapi import HTTPException, status


def execute(db: Connection, user_id: int, data: dict):
    try:
        if data.get("currency_id"):
            get_currency_service.execute(db, data["currency_id"])

        if data.get("language_id"):
            get_language_service.execute(db, data["language_id"])

        if data.get("timezone_id"):
            get_timezone_service.execute(db, data["timezone_id"])

        person_data = data.pop("person", None)
        if person_data:
            if person_data.get("name"):
                person_data["person_name"] = person_data.pop("name")

            if person_data.get("gender_id"):
                get_gender_service.execute(db, person_data["gender_id"])

            user = get_user_service.execute(db, user_id)
            person_id = user["person"]["id"]

            updated_person_id = update_person(db, person_id, person_data)
            if not updated_person_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update person data",
                )

        if data:
            updated_user_id = update_user(db, user_id, data)
            if not updated_user_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user data",
                )

        return {"message": "User data updated successfully"}
    except HTTPException as e:
        print(e)
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user data",
        )
