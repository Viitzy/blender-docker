from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection
from account.src.crud.properties_tables.companies import update_company
from account.src.crud.properties_tables.company_users import (
    get_company_by_user_id,
)


def execute(db: Connection, user_id: int, data: dict):
    company = get_company_by_user_id(db, user_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    company_id = company["company_id"]

    if data.get("name"):
        data["company_name"] = data.pop("name")

    if data.get("creci"):
        data["document_number"] = data.pop("creci")

    update_company(db, company_id, data)

    return {"message": "Company updated successfully"}
