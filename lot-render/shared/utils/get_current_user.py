from fastapi import Depends, HTTPException, status
from shared.utils.jwt_decoder import get_jwt_payload
from fastapi.security import OAuth2PasswordBearer
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Create a mock request with the token
        class MockRequest:
            def __init__(self, token):
                if not token.startswith("Bearer "):
                    token = f"Bearer {token}"
                self.headers = {"Authorization": token}

        request = MockRequest(token)

        # Use the shared jwt_decoder
        payload = get_jwt_payload(request)

        # Convert sub to int if it exists
        user_id = (
            int(payload.get("sub")) if payload.get("sub") is not None else None
        )
        if user_id is None:
            raise credentials_exception

        return user_id

    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error:", str(e))
        raise credentials_exception
