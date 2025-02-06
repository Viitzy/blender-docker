from psycopg2.extensions import connection as Connection
from account.src.crud.global_tables.person_contacts import create_person_contact


def execute(db: Connection, person_contact_data: dict):
    person_contact_id = create_person_contact(db, person_contact_data)
    return person_contact_id
