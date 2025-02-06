from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Sequence,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from shared.database.connections import Base


class ExternalProvider(Base):
    __tablename__ = "external_providers"
    __table_args__ = {"schema": "authentication"}

    external_provider_id = Column(
        Integer,
        Sequence("external_providers_seq", schema="authentication"),
        primary_key=True,
    )
    external_provider_name = Column(String(50), nullable=False, unique=True)
    ws_endpoint = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    user_external_providers = relationship(
        "UserExternalProvider", back_populates="external_providers"
    )


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "authentication"}

    role_id = Column(
        Integer,
        Sequence("roles_seq", schema="authentication"),
        primary_key=True,
    )
    role_name = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    user_roles = relationship("UserRole", back_populates="roles")


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "authentication"}

    user_id = Column(
        Integer,
        Sequence("users_seq", schema="authentication"),
        primary_key=True,
        index=True,
    )
    person_id = Column(
        Integer, ForeignKey("global.people.person_id"), nullable=False
    )
    username = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)
    language_id = Column(
        Integer, ForeignKey("global.language.language_id"), nullable=False
    )
    currency_id = Column(
        Integer, ForeignKey("global.currency.currency_id"), nullable=False
    )
    timezone_id = Column(
        Integer, ForeignKey("global.timezone.timezone_id"), nullable=False
    )
    userstatus_id = Column(
        Integer,
        ForeignKey("authentication.userstatus.userstatus_id"),
        nullable=False,
    )
    email_confirmed = Column(Boolean, default=False, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    person = relationship("Person", back_populates="user")
    user_status = relationship("UserStatus", back_populates="users")
    language = relationship("Language", back_populates="users")
    currency = relationship("Currency", back_populates="users")
    timezone = relationship("Timezone", back_populates="users")
    notifications = relationship("UserNotification", back_populates="users")
    user_roles = relationship("UserRole", back_populates="users")
    user_external_providers = relationship(
        "UserExternalProvider", back_populates="users"
    )


class UserExternalProvider(Base):
    __tablename__ = "user_external_providers"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "external_provider_id",
            name="external_providers_name_idx1",
        ),
        {"schema": "authentication"},
    )

    user_external_providers_id = Column(
        Integer,
        Sequence("user_external_providers_seq", schema="authentication"),
        primary_key=True,
    )
    user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    external_provider_id = Column(
        Integer,
        ForeignKey("authentication.external_providers.external_provider_id"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    users = relationship("User", back_populates="user_external_providers")
    external_providers = relationship(
        "ExternalProvider", back_populates="user_external_providers"
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="user_roles_idx"),
        {"schema": "authentication"},
    )

    user_role_id = Column(
        Integer,
        Sequence("user_roles_seq", schema="authentication"),
        primary_key=True,
    )
    user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    role_id = Column(
        Integer, ForeignKey("authentication.roles.role_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    users = relationship("User", back_populates="user_roles")
    roles = relationship("Role", back_populates="user_roles")


class UserStatus(Base):
    __tablename__ = "userstatus"
    __table_args__ = {"schema": "authentication"}

    userstatus_id = Column(
        Integer,
        Sequence("userstatus_seq", schema="authentication"),
        primary_key=True,
        index=True,
    )
    userstatus_name = Column(String(70), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    users = relationship("User", back_populates="user_status")
