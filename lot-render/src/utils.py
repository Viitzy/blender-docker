import bcrypt
from datetime import datetime
import pandas as pd
import re


def mask_email(email: str) -> str:
    email_user, email_domain = email.split("@", 1)
    user_length = len(email_user)
    if user_length <= 1:
        masked_email = "*" + "@" + email_domain
    elif user_length == 2:
        masked_email = email_user[0] + "*" + "@" + email_domain
    else:
        masked_email = (
            email_user[0]
            + "*" * min(user_length - 2, 3)
            + email_user[-1]
            + "@"
            + email_domain
        )
    return masked_email


def mask_phone(phone: str) -> str:
    phone_length = len(phone)

    if phone_length <= 4:
        masked_phone = "*" * phone_length
    else:
        masked_phone = (
            "".join(
                [
                    " " if char in "()" else char if char == "-" else "*"
                    for char in phone[:-4]
                ]
            )
            + phone[-4:]
        )

    return masked_phone


def mask_contact_value(contact_value: str) -> str:
    masked_contact_value = ""

    contact_value = contact_value.replace(" ", "")

    if "@" in contact_value and validate_email(contact_value):
        masked_contact_value = mask_email(contact_value)
    else:
        masked_contact_value = mask_phone(contact_value)

    return masked_contact_value


def format_email(email: str) -> str:
    return email.lower()


def format_phone(ddi: str, phone: str) -> str:
    return f"{ddi} {phone}"


def validate_email(email: str) -> bool:
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"

    if not re.fullmatch(regex, email):
        return False

    return True


def hash_password(password: str) -> tuple:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8"), salt.decode("utf-8")


def verify_password(
    plain_password: str, hashed_password: str, salt: str
) -> bool:
    return (
        bcrypt.hashpw(
            plain_password.encode("utf-8"), salt.encode("utf-8")
        ).decode("utf-8")
        == hashed_password
    )


def dict_to_df(data: dict) -> pd.DataFrame:
    prepared_data = {}
    for key, value in data.items():
        if isinstance(value, list):
            prepared_data[key] = [", ".join(map(str, value))]
        else:
            prepared_data[key] = [value]

    return pd.DataFrame(prepared_data)


def format_dict(data: dict) -> dict:
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = datetime.strftime(value, format="%d/%m/%Y")
    return data


def normalize_email(email: str) -> str:
    return re.sub(r"\s+", "", email.lower())


def normalize_phone(phone: str) -> str:
    return re.sub(r"[^\d]", "", phone)


def normalize_contact_value(contact_value: str) -> str:
    if "@" in contact_value:
        return normalize_email(contact_value)

    return normalize_phone(contact_value)
