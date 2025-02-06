from psycopg2.extensions import connection as Connection
from account.src.crud.authentication_tables.users import get_user_by_username
from account.src.crud.authentication_tables.user_external_providers import (
    get_user_external_provider,
)
from utils import normalize_contact_value


def execute(db: Connection, username: str):
    normalized_username = normalize_contact_value(username)

    user = get_user_by_username(db, normalized_username)
    if not user:
        return {"exists": False, "provider": None, "role_id": None}

    external_provider = get_user_external_provider(db, user["user_id"])
    return {
        "exists": True,
        "provider": "google" if external_provider else None,
        "role_id": user["role_id"],
    }
