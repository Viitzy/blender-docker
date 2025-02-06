from datetime import datetime
from psycopg2.extensions import connection as Connection
import random
from account.src.crud.properties_tables.company_contacts import (
    update_company_contact,
)
from account.src.services.users import delete_user_service
from account.src.services.companies import (
    update_company_service,
    get_company_service,
)
from account.src.services.sessions import delete_all_sessions_service
from shared.database.mongo import MongoClient


def execute(db: Connection, user_id: int):
    company = get_company_service.execute(db, user_id)

    company_phones = []
    if company["contacts"]:
        for contact in company["contacts"]:
            if contact["type"]["name"].lower() == "telefone":
                company_phones.append(contact["value"])

            update_company_contact(
                db,
                contact["id"],
                "".join(random.sample(contact["value"], len(contact["value"]))),
            )

    mongo_client = MongoClient("gethome-01")
    mongo_client.insert_one(
        "excluded_companies",
        {
            "company_name": company["name"],
            "created_at": datetime.now(),
            "company_phones": company_phones,
        },
    )

    update_company_service.execute(
        db,
        user_id,
        {
            "name": (
                f'{"".join(random.sample(company["name"], len(company["name"])))}#deleted'
                if company["name"]
                else None
            ),
            "cnpj": (
                "".join(random.sample(company["cnpj"], len(company["cnpj"])))
                if company["cnpj"]
                else None
            ),
            "website": (
                "".join(
                    random.sample(company["website"], len(company["website"]))
                )
                if company["website"]
                else None
            ),
            "document_number": (
                "".join(random.sample(company["creci"], len(company["creci"])))
                if company["creci"]
                else None
            ),
        },
    )

    delete_all_sessions_service.execute(db, user_id)
    delete_user_service.execute(db, user_id)

    return {"message": "Company deleted successfully"}
