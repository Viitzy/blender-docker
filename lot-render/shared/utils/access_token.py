from fastapi import Depends
from datetime import datetime, timedelta
from jose import jwt
import os
import logging
from shared.utils.get_api_key import get_api_key

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = "HS256"


def create_access_token(
    data: dict,
    expires_delta: timedelta = None,
    dependencies=[Depends(get_api_key)],
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
