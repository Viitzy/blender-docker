from decimal import Decimal
from sqlalchemy.engine.row import Row
from datetime import datetime, date
from typing import Any


def json_encoder(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, Row):
        return dict(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    elif hasattr(obj, "__dict__"):
        return vars(obj)
    raise TypeError(
        f"Object of type {type(obj).__name__} is not JSON serializable"
    )
