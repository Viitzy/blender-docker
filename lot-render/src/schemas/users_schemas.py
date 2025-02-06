from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional, List

from account.src.schemas.people_schemas import PersonResponse, PersonUpdate
from account.src.schemas.user_status_schemas import UserStatusResponse
from account.src.schemas.languages_schemas import LanguageResponse
from account.src.schemas.currencies_schemas import CurrencyResponse
from account.src.schemas.timezones_schemas import TimezoneResponse
from account.src.schemas.roles_schemas import RoleResponse


class UserResponse(BaseModel):
    user_id: int
    login_type: str
    person: PersonResponse
    status: UserStatusResponse
    language: LanguageResponse
    currency: CurrencyResponse
    timezone: TimezoneResponse
    roles: Optional[List[RoleResponse]] = Field(default=None)
    email_confirmed: Optional[bool] = Field(default=None)
    phone_confirmed: Optional[bool] = Field(default=None)
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "person_id": 1,
                "username": "pparker",
                "language_id": 1,
                "currency_id": 1,
                "timezone_id": 1,
                "userstatus_id": 1,
                "roles": [{"id": 1, "name": "Admin"}],
                "email_confirmed": True,
                "phone_confirmed": True,
                "created_at": "2024-07-15T17:34:56",
                "updated_at": "2024-07-15T17:34:56",
            }
        }


class UserPasswordUpdate(BaseModel):
    current_password: str = None
    new_password: str = None
    confirm_new_password: str = None


class UserUpdate(BaseModel):
    person: Optional[PersonUpdate] = Field(default=None)
    currency_id: Optional[int] = Field(default=None)
    timezone_id: Optional[int] = Field(default=None)
    language_id: Optional[int] = Field(default=None)
    userstatus_id: Optional[int] = Field(default=None)
    email_confirmed: Optional[bool] = Field(default=None)
    phone_confirmed: Optional[bool] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "pparker",
                "person": {
                    "name": "Peter Parker",
                    "preferred_name": "Spider-Man",
                    "profile_picture": "https://example.com/spider-man.jpg",
                    "gender_id": 1,
                },
                "currency_id": 1,
                "timezone_id": 1,
                "language_id": 1,
                "userstatus_id": 1,
                "email_confirmed": True,
                "phone_confirmed": True,
            }
        }


class UserUpdateResponse(BaseModel):
    message: str


class UserReportCreate(BaseModel):
    file_type: Literal["csv", "json", "pdf"]

    class Config:
        json_schema_extra = {
            "example": {
                "file_type": "csv",
            }
        }


class UserReportResponse(BaseModel):
    class File(BaseModel):
        filename: str
        content: str
        file_type: str

    message: str
    file: File

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Success",
                "file": {
                    "filename": "uuid4.csv",
                    "content": "base64encodedcontent",
                    "mime_type": "text/csv",
                },
            }
        }


class UserExistsResponse(BaseModel):
    exists: bool
    provider: Optional[str] = Field(default=None)
    role_id: Optional[int] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "exists": True,
                "provider": "google",
                "role_id": 1,
            }
        }


class UserDeleteResponse(BaseModel):
    message: str
