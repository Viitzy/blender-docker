import bcrypt


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
