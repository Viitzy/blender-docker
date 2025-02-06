from psycopg2.extensions import connection as Connection
from account.src.crud.properties_tables.company_contacts import (
    create_company_contact,
)


def execute(db: Connection, data: dict):
    company_contact_id = create_company_contact(db, data)
    return company_contact_id
