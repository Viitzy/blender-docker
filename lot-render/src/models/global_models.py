from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Sequence,
    String,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from shared.database.connections import Base


class ContactType(Base):
    __tablename__ = "contact_types"
    __table_args__ = (
        UniqueConstraint(
            "contact_type_name", name="contact_type_contact_type_name_idx"
        ),
        {"schema": "global"},
    )

    contact_type_id = Column(
        Integer,
        Sequence("contact_types_seq", schema="global"),
        primary_key=True,
    )
    contact_type_name = Column(String(50), nullable=False, unique=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    person_contacts = relationship(
        "PersonContact", back_populates="contact_type"
    )


class Currency(Base):
    __tablename__ = "currency"
    __table_args__ = (
        UniqueConstraint("currency_name", name="currency_currency_name_idx"),
        {"schema": "global"},
    )

    currency_id = Column(
        Integer,
        Sequence("currency_seq", schema="global"),
        primary_key=True,
        index=True,
    )
    currency_name = Column(String(70), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    users = relationship("User", back_populates="currency")


class Language(Base):
    __tablename__ = "language"
    __table_args__ = (
        UniqueConstraint("language_name", name="language_language_name_idx"),
        {"schema": "global"},
    )

    language_id = Column(
        Integer,
        Sequence("language_seq", schema="global"),
        primary_key=True,
        index=True,
    )
    language_name = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    users = relationship("User", back_populates="language")


class NotificationType(Base):
    __tablename__ = "notification_type"
    __table_args__ = (
        UniqueConstraint(
            "notification_type_name", name="notification_type_name_idx"
        ),
        {"schema": "global"},
    )

    notification_type_id = Column(
        Integer,
        Sequence("notification_type_seq", schema="authentication"),
        primary_key=True,
    )
    notification_type_name = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    notifications = relationship(
        "UserNotification", back_populates="notification_type"
    )


class Person(Base):
    __tablename__ = "people"
    __table_args__ = (
        UniqueConstraint("identification", name="people_identification_idx"),
        {"schema": "global"},
    )

    person_id = Column(
        Integer,
        Sequence("people_seq", schema="global"),
        primary_key=True,
        index=True,
    )
    person_name = Column(String(150), nullable=False)
    identification = Column(String(15), nullable=True, unique=True)
    preferred_name = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    contacts = relationship("PersonContact", back_populates="person")
    user = relationship("User", back_populates="person")


class PersonContact(Base):
    __tablename__ = "person_contacts"
    __table_args__ = (
        UniqueConstraint(
            "contact_value", name="person_contacts_contact_value_idx"
        ),
        {"schema": "global"},
    )

    person_contact_id = Column(
        Integer,
        Sequence("person_contacts_seq", schema="global"),
        primary_key=True,
        index=True,
    )
    person_id = Column(
        Integer, ForeignKey("global.people.person_id"), nullable=False
    )
    contact_type_id = Column(
        Integer,
        ForeignKey("global.contact_types.contact_type_id"),
        nullable=False,
    )
    contact_value = Column(String(150), nullable=True)
    ind_primary_contact = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    person = relationship("Person", back_populates="contacts")
    contact_type = relationship("ContactType", back_populates="person_contacts")


class Timezone(Base):
    __tablename__ = "timezone"
    __table_args__ = (
        UniqueConstraint("timezone_name", name="timezone_timezone_name_idx"),
        {"schema": "global"},
    )

    timezone_id = Column(
        Integer,
        Sequence("timezone_seq", schema="global"),
        primary_key=True,
        index=True,
    )
    timezone_name = Column(String(70), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    users = relationship("User", back_populates="timezone")


class UserNotification(Base):
    __tablename__ = "user_notifications"
    __table_args__ = {"schema": "global"}

    user_notification_id = Column(
        Integer,
        Sequence("user_notifications_seq", schema="authentication"),
        primary_key=True,
    )
    user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    notification_type_id = Column(
        Integer,
        ForeignKey("global.notification_type.notification_type_id"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)

    notification_type = relationship(
        "NotificationType", back_populates="notifications"
    )
    users = relationship("User", back_populates="notifications")
