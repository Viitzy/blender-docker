from fastapi import HTTPException, status
from psycopg2.extensions import connection as Connection
from account.src.crud.properties_tables.companies import get_company
from account.src.crud.properties_tables.company_users import (
    get_company_by_user_id,
)
from account.src.services.contacts.company_contacts import (
    list_company_contacts_service,
)


def execute(db: Connection, user_id: int):
    company_user = get_company_by_user_id(db, user_id)
    if not company_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    company = get_company(db, company_user["company_id"])
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    company = {
        "id": company["company_id"],
        "name": company["company_name"],
        "cnpj": company["cnpj"],
        "company_type": {
            "id": company["company_type_id"],
            "name": company["company_type_name"],
        },
        "website": company["website"],
        "href": company["href"],
        "creci": company["document_number"],
        "address": (
            {
                "id": company["address_id"],
                "street": company["street_name"],
                "number": company["number"],
                "complement": company["complement"],
                "neighborhood": company["neighborhood_name"],
                "city": {
                    "id": company["city_id"],
                    "name": company["city_name"],
                    "state": {
                        "id": company["state_id"],
                        "name": company["state_name"],
                        "country": {
                            "id": company["country_id"],
                            "name": company["country_name"],
                        },
                    },
                },
                "formatted_address": (
                    f"{company['street_name'] if company['street_name'] else ''}"
                    f"{', ' if company['number'] else ''}"
                    f"{company['number'] if company['number'] else ''}"
                    f"{', ' if company['complement'] and company['number'] else ''}"
                    f"{company['complement'] if company['complement'] and company['number'] else ''}"
                    f"{' - ' if company['street_name'] or company['number'] else ''}"
                    f"{company['neighborhood_name']}, "
                    f"{company['city_name']} - "
                    f"{company['state_name']}, "
                    f"{company['country_name']}"
                ),
            }
            if company["address_id"]
            else None
        ),
        "created_at": company["company_created_at"],
        "updated_at": company["company_updated_at"],
    }

    company_contacts = list_company_contacts_service.execute(db, company["id"])
    if company_contacts["company_contacts"]:
        company["contacts"] = company_contacts["company_contacts"]

    return company
