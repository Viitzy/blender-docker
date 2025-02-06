from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection

from account.src.crud.authentication_tables.roles import get_role


def execute(db: Connection, role_id: int):
    role = get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return {"id": role["role_id"], "name": role["role_name"]}
