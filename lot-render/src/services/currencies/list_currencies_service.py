from psycopg2.extensions import connection as Connection
from account.src.crud.global_tables.currencies import list_currencies


def execute(db: Connection):
    currencies = list_currencies(db)
    return {
        "currencies": [
            {"id": currency["currency_id"], "name": currency["currency_name"]}
            for currency in currencies
        ]
    }
