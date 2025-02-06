from sqlalchemy.orm import Session
from properties.src.crud.properties_tables.lots import get_lot_details


def execute(db: Session, lot_id: int):
    return get_lot_details(db, lot_id)
