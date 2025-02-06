import re
import password_strength


def is_email_or_phone(login_field: str) -> str:
    """Determine if the login_field is an email or a phone number."""
    email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    phone_regex = r"^\+?[1-9]\d{1,14}$"  # Basic phone number regex

    if re.fullmatch(email_regex, login_field):
        return "email"
    elif re.fullmatch(phone_regex, login_field):
        return "phone"
    else:
        return "invalid"


def validate_password(password: str) -> bool:
    policy = password_strength.PasswordPolicy.from_names(
        length=8,
        # uppercase=1,
        # numbers=1,
        # special=1,
    )
    errors = policy.test(password)
    if errors:
        return str([f"- {error}" for error in errors])

    return None
