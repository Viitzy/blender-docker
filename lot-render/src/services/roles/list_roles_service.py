from psycopg2.extensions import connection as Connection

from account.src.crud.authentication_tables.roles import list_roles


def execute(db: Connection):
    roles = list_roles(db)
    return {
        "roles": [
            {"id": role["role_id"], "name": role["role_name"]} for role in roles
        ]
    }
