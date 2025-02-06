from datetime import datetime
from sqlalchemy import (
    Boolean,
    CHAR,
    Column,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Sequence,
    TIMESTAMP,
    UniqueConstraint,
    Text,
    VARCHAR,
)
from sqlalchemy.orm import relationship
from shared.database.connections import Base
from sqlalchemy import DateTime


# Authentication models
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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    person = relationship("Person", back_populates="user")
    company_users = relationship("CompanyUser", back_populates="user")
    user_status = relationship("UserStatus", back_populates="users")
    language = relationship("Language", back_populates="users")
    currency = relationship("Currency", back_populates="users")
    timezone = relationship("Timezone", back_populates="users")
    notifications = relationship("UserNotification", back_populates="users")
    user_roles = relationship("UserRole", back_populates="users")
    user_external_providers = relationship(
        "UserExternalProvider", back_populates="users"
    )

    verification_tokens = relationship(
        "VerificationToken", back_populates="user"
    )
    sessions = relationship("Session", back_populates="user")
    # social_authentications = relationship("SocialAuthentication", back_populates="user")

    lot_seller = relationship("LotSeller", back_populates="user")


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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    users = relationship("User", back_populates="user_status")


# Global models
class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (
        UniqueConstraint(
            "street", "number", "city_id", name="street_number_city_idx"
        ),
        {"schema": "global"},
    )

    address_id = Column(
        Integer, Sequence("addresses_seq", schema="global"), primary_key=True
    )
    street = Column(String(255), nullable=False)
    number = Column(Integer, nullable=True)
    complement = Column(String(255), nullable=True)
    neighborhood = Column(String(255), nullable=True)
    city_id = Column(
        Integer, ForeignKey("global.cities.city_id"), nullable=False
    )
    postal_code = Column(String(20), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    city = relationship("City")
    companies = relationship("Company", back_populates="address")
    lot_address_history = relationship(
        "LotAddressHistory", back_populates="address"
    )
    lots = relationship("Lot", back_populates="address")
    requests = relationship("LotAddressRequest", back_populates="address")


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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    person_contacts = relationship(
        "PersonContact", back_populates="contact_type"
    )


class City(Base):
    __tablename__ = "cities"
    __table_args__ = (
        UniqueConstraint("city_name", "state_id", name="city_name_idx"),
        {"schema": "global"},
    )

    city_id = Column(
        Integer, Sequence("cities_seq", schema="global"), primary_key=True
    )
    city_name = Column(String(255), nullable=False)
    state_id = Column(
        Integer, ForeignKey("global.states.state_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    state = relationship("State")
    addresses = relationship("Address", back_populates="city")


class Country(Base):
    __tablename__ = "countries"
    __table_args__ = (
        UniqueConstraint("country_name", name="country_name_idx"),
        {"schema": "global"},
    )

    country_id = Column(
        Integer, Sequence("countries_seq", schema="global"), primary_key=True
    )
    country_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    states = relationship("State", back_populates="country")


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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    profile_picture = Column(String(500))
    gender_id = Column(Integer, ForeignKey("global.gender.gender_id"))
    birth_date = Column(DateTime, nullable=False, default="1900-01-01 00:00:00")

    contacts = relationship("PersonContact", back_populates="person")
    user = relationship("User", back_populates="person")
    gender = relationship("Gender", back_populates="gender_users")


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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    person = relationship("Person", back_populates="contacts")
    contact_type = relationship("ContactType", back_populates="person_contacts")


class ReferenceIdentifier(Base):
    __tablename__ = "reference_identifier"
    __table_args__ = {"schema": "global"}  # Especifica o schema

    reference_identifier_id = Column(
        Integer, Sequence("global.reference_identifier_seq"), primary_key=True
    )
    reference = Column(String(40), nullable=False)
    value = Column(String(40), nullable=False)
    description = Column(String(200), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP)


class Region(Base):
    __tablename__ = "regions"
    __table_args__ = (
        UniqueConstraint("region_name", name="region_name_idx"),
        {"schema": "global"},
    )

    region_id = Column(
        Integer, Sequence("regions_seq", schema="global"), primary_key=True
    )
    region_name = Column(String(255), nullable=False)
    region_type_id = Column(
        Integer,
        ForeignKey("global.region_types.region_type_id"),
        nullable=False,
    )
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    region_type = relationship("RegionType", back_populates="regions")
    lots = relationship("Lot", back_populates="region")


class RegionType(Base):
    __tablename__ = "region_types"
    __table_args__ = (
        UniqueConstraint("region_type_name", name="region_type_name_idx"),
        {"schema": "global"},
    )

    region_type_id = Column(
        Integer, Sequence("region_types_seq", schema="global"), primary_key=True
    )
    region_type_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    regions = relationship("Region", back_populates="region_type")


class State(Base):
    __tablename__ = "states"
    __table_args__ = (
        UniqueConstraint("state_name", name="state_name_idx"),
        {"schema": "global"},
    )

    state_id = Column(
        Integer, Sequence("states_seq", schema="global"), primary_key=True
    )
    state_name = Column(String(100), nullable=False)
    country_id = Column(
        Integer, ForeignKey("global.countries.country_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    country = relationship("Country", back_populates="states")
    cities = relationship("City", back_populates="state")


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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

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
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    notification_type = relationship(
        "NotificationType", back_populates="notifications"
    )
    users = relationship("User", back_populates="notifications")


# Properties models
class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("company_name", name="company_name_idx"),
        {"schema": "properties"},
    )

    company_id = Column(
        Integer,
        Sequence("companies_seq", schema="properties"),
        primary_key=True,
    )
    company_name = Column(String(255), nullable=False)
    company_type_id = Column(
        Integer,
        ForeignKey("properties.company_types.company_type_id"),
        nullable=False,
    )
    cnpj = Column(String(14), nullable=True)
    address_id = Column(
        Integer, ForeignKey("global.addresses.address_id"), nullable=False
    )
    website = Column(String(255), nullable=True)
    href = Column(String(200), nullable=True)
    creci = Column(String(30), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    company_type = relationship("CompanyType")
    address = relationship("Address")
    contacts = relationship("CompanyContact", back_populates="company")
    company_users = relationship("CompanyUser", back_populates="company")


class CompanyContact(Base):
    __tablename__ = "company_contacts"
    __table_args__ = (
        UniqueConstraint("contact_value", name="contact_value_idx"),
        {"schema": "properties"},
    )

    company_contact_id = Column(
        Integer,
        Sequence("company_contacts_seq", schema="properties"),
        primary_key=True,
    )
    company_id = Column(
        Integer, ForeignKey("properties.companies.company_id"), nullable=False
    )
    contact_type_id = Column(
        Integer,
        ForeignKey("global.contact_types.contact_type_id"),
        nullable=False,
    )
    contact_value = Column(String(250), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    company = relationship("Company", back_populates="contacts")
    contact_type = relationship("ContactType")


class CompanyUser(Base):
    __tablename__ = "company_users"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "user_id", "seller_type_id", name="company_users_idx1"
        ),
        {"schema": "properties"},
    )

    company_users_id = Column(
        Integer,
        Sequence("company_users_seq", schema="properties"),
        primary_key=True,
    )
    company_id = Column(
        Integer, ForeignKey("properties.companies.company_id"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    seller_type_id = Column(
        Integer,
        ForeignKey("properties.seller_type.seller_type_id"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    company = relationship("Company", back_populates="company_users")
    user = relationship("User", back_populates="company_users")
    seller_type = relationship("SellerType", back_populates="company_users")


class CompanyType(Base):
    __tablename__ = "company_types"
    __table_args__ = (
        UniqueConstraint("company_type_name", name="company_type_name_idx"),
        {"schema": "properties"},
    )

    company_type_id = Column(
        Integer,
        Sequence("company_types_seq", schema="properties"),
        primary_key=True,
    )
    company_type_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    companies = relationship("Company", back_populates="company_type")


class LotAddressHistory(Base):
    __tablename__ = "lot_address_history"
    __table_args__ = {"schema": "properties"}

    lot_address_history_id = Column(
        Integer,
        Sequence("lot_address_history_seq", schema="properties"),
        primary_key=True,
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    address_id = Column(
        Integer, ForeignKey("global.addresses.address_id"), nullable=False
    )
    modified_by_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    lot = relationship("Lot")
    address = relationship("Address")
    modified_by_user = relationship("User")


class LotAddressRequest(Base):
    __tablename__ = "lot_address_requests"
    __table_args__ = {"schema": "properties"}

    lot_address_requests_id = Column(
        Integer,
        Sequence("lot_address_requests_seq", schema="properties"),
        primary_key=True,
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    address_id = Column(
        Integer, ForeignKey("global.addresses.address_id"), nullable=True
    )
    responsible_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=True
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    lot = relationship("Lot", back_populates="address_requests")
    address = relationship("Address", back_populates="requests")
    responsible_user = relationship(
        "User",
        foreign_keys=[responsible_user_id],
        backref="lot_address_req_responsible_user",
    )
    status_history = relationship(
        "LotAddressRequestStatusHistory",
        back_populates="lot_address_request",
        order_by="desc(LotAddressRequestStatusHistory.lot_address_request_status_history_id)",
    )
    applicants = relationship(
        "LotAddressRequestUsers", back_populates="lot_address_request"
    )


class LotAddressRequestStatus(Base):
    __tablename__ = "lot_address_request_status"
    __table_args__ = (
        UniqueConstraint(
            "lot_address_request_status_name",
            name="lot_address_request_status_name_idx",
        ),
        {"schema": "properties"},
    )

    lot_address_request_status_id = Column(
        Integer,
        Sequence("lot_address_request_status_seq", schema="properties"),
        primary_key=True,
    )
    lot_address_request_status_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    request_status_history = relationship(
        "LotAddressRequestStatusHistory", back_populates="request_status"
    )


class LotAddressRequestStatusHistory(Base):
    __tablename__ = "lot_address_request_status_history"
    __table_args__ = {"schema": "properties"}

    lot_address_request_status_history_id = Column(
        Integer,
        Sequence("lot_address_request_status_history_seq", schema="properties"),
        primary_key=True,
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )

    lot_address_requests_id = Column(
        Integer,
        ForeignKey("properties.lot_address_requests.lot_address_requests_id"),
        nullable=False,
    )
    lot_address_request_status_id = Column(
        Integer,
        ForeignKey(
            "properties.lot_address_request_status.lot_address_request_status_id"
        ),
        nullable=False,
    )
    modified_by_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    request_status = relationship(
        "LotAddressRequestStatus", back_populates="request_status_history"
    )
    modified_by_user = relationship(
        "User",
        foreign_keys=[modified_by_user_id],
        backref="modified_status_histories",
    )
    lot_address_request = relationship(
        "LotAddressRequest", back_populates="status_history"
    )


class LotAddressRequestUsers(Base):
    __tablename__ = "lot_address_request_users"
    __table_args__ = (
        UniqueConstraint(
            "lot_address_requests_id",
            "user_id",
            name="lot_address_request_users_seq_user_id_idx",
        ),
        {"schema": "properties"},
    )

    lot_address_request_users_id = Column(
        Integer,
        Sequence("lot_address_request_users_seq", schema="properties"),
        primary_key=True,
    )
    lot_address_requests_id = Column(
        Integer,
        ForeignKey("properties.lot_address_requests.lot_address_requests_id"),
        nullable=False,
    )
    user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    lot_address_request = relationship(
        "LotAddressRequest", back_populates="applicants"
    )
    user = relationship("User")


class LotAreaHistory(Base):
    __tablename__ = "lot_area_history"
    __table_args__ = {"schema": "properties"}

    lot_area_history_id = Column(
        Integer,
        Sequence("lot_area_history_seq", schema="properties"),
        primary_key=True,
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    area = Column(Numeric(10, 2), nullable=False)
    modified_by_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    lot = relationship("Lot")
    modified_by_user = relationship("User")


class LotPriceHistory(Base):
    __tablename__ = "lot_price_history"
    __table_args__ = {"schema": "properties"}

    lot_price_history_id = Column(
        Integer,
        Sequence("lot_price_history_seq", schema="properties"),
        primary_key=True,
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    price = Column(Numeric(10, 2), nullable=False)
    modified_by_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    lot = relationship("Lot")
    modified_by_user = relationship("User")


class Lot(Base):
    __tablename__ = "lots"
    __table_args__ = {"schema": "properties"}

    lot_id = Column(
        Integer, Sequence("lots_seq", schema="properties"), primary_key=True
    )
    region_id = Column(
        Integer, ForeignKey("global.regions.region_id"), nullable=False
    )
    title = Column(String(255), nullable=False)
    link = Column(String(255), nullable=True)
    condominium_fee = Column(Numeric(10, 2), nullable=True)
    viva_real_code = Column(String(255), nullable=True)
    processed = Column(CHAR(1), nullable=False, default="N")
    address_id = Column(
        Integer, ForeignKey("global.addresses.address_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    region = relationship("Region")
    address = relationship("Address")
    price_history = relationship(
        "LotPriceHistory",
        back_populates="lot",
        order_by="desc(LotPriceHistory.lot_price_history_id)",
    )
    area_history = relationship(
        "LotAreaHistory",
        back_populates="lot",
        order_by="desc(LotAreaHistory.lot_area_history_id)",
    )
    status_history = relationship(
        "LotStatusHistory",
        back_populates="lot",
        order_by="desc(LotStatusHistory.lot_status_history_id)",
    )
    address_history = relationship(
        "LotAddressHistory",
        back_populates="lot",
        order_by="desc(LotAddressHistory.lot_address_history_id)",
    )
    visits = relationship("LotVisit", back_populates="lot")
    lot_sellers = relationship("LotSeller", back_populates="lot")
    address_requests = relationship("LotAddressRequest", back_populates="lot")


class LotSeller(Base):
    __tablename__ = "lot_sellers"
    __table_args__ = (
        UniqueConstraint(
            "lot_id", "user_id", "seller_type_id", name="lot_sellers_idx1"
        ),
        {"schema": "properties"},
    )

    lot_sellers_id = Column(
        Integer,
        Sequence("lot_sellers_seq", schema="properties"),
        primary_key=True,
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    seller_type_id = Column(
        Integer,
        ForeignKey("properties.seller_type.seller_type_id"),
        nullable=False,
    )
    company_reference = Column(String(20), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    lot = relationship("Lot", back_populates="lot_sellers")
    user = relationship("User", back_populates="lot_seller")
    seller_type = relationship("SellerType", back_populates="lot_sellers")


class LotStatus(Base):
    __tablename__ = "lot_status"
    __table_args__ = (
        UniqueConstraint("lot_status_name", name="lot_status_name_idx"),
        {"schema": "properties"},
    )

    lot_status_id = Column(
        Integer,
        Sequence("lot_status_seq", schema="properties"),
        primary_key=True,
    )
    lot_status_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    status_history = relationship(
        "LotStatusHistory", back_populates="lot_status"
    )


class LotStatusHistory(Base):
    __tablename__ = "lot_status_history"
    __table_args__ = {"schema": "properties"}

    lot_status_history_id = Column(
        Integer,
        Sequence("lot_status_history_seq", schema="properties"),
        primary_key=True,
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    lot_status_id = Column(
        Integer,
        ForeignKey("properties.lot_status.lot_status_id"),
        nullable=False,
    )
    modified_by_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    lot = relationship("Lot", back_populates="status_history")
    lot_status = relationship("LotStatus", back_populates="status_history")
    modified_by_user = relationship("User")


class LotVisit(Base):
    __tablename__ = "lot_visits"
    __table_args__ = {"schema": "properties"}

    lot_visit_id = Column(
        Integer,
        Sequence("lot_visits_seq", schema="properties"),
        primary_key=True,
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    responsible_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=True
    )
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    lot = relationship("Lot", back_populates="visits")

    user = relationship(
        "User",
        foreign_keys=[user_id],
        backref="lot_visit_request_user",
    )
    status_history = relationship(
        "LotVisitStatusHistory",
        back_populates="lot_visit",
        order_by="desc(LotVisitStatusHistory.lot_visit_status_history_id)",
    )
    responsible_user = relationship(
        "User",
        foreign_keys=[responsible_user_id],
        backref="lot_visit_responsible_lot_visits",
    )


class LotVisitStatusHistory(Base):
    __tablename__ = "lot_visit_status_history"
    __table_args__ = {"schema": "properties"}

    lot_visit_status_history_id = Column(
        Integer,
        Sequence("lot_visit_status_history_seq", schema="properties"),
        primary_key=True,
    )
    lot_visit_id = Column(
        Integer,
        ForeignKey("properties.lot_visits.lot_visit_id"),
        nullable=False,
    )
    visit_status_id = Column(
        Integer,
        ForeignKey("properties.visit_status.visit_status_id"),
        nullable=False,
    )
    visit_date = Column(TIMESTAMP, nullable=False)
    suggested_visit_dates = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    lot_visit = relationship("LotVisit", back_populates="status_history")
    visit_status = relationship("VisitStatus")


class SellerType(Base):
    __tablename__ = "seller_type"
    __table_args__ = (
        UniqueConstraint("seller_type_name", name="seller_type_seq_idx"),
        {"schema": "properties"},
    )

    seller_type_id = Column(
        Integer,
        Sequence("seller_type_seq", schema="properties"),
        primary_key=True,
    )

    seller_type_name = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    company_users = relationship("CompanyUser", back_populates="seller_type")
    lot_sellers = relationship("LotSeller", back_populates="seller_type")


class VisitStatus(Base):
    __tablename__ = "visit_status"
    __table_args__ = (
        UniqueConstraint("visit_status_name", name="visit_status_name_idx"),
        {"schema": "properties"},
    )

    visit_status_id = Column(
        Integer,
        Sequence("visit_status_seq", schema="properties"),
        primary_key=True,
    )
    visit_status_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    visit_status_history = relationship(
        "LotVisitStatusHistory", back_populates="visit_status"
    )


class VerificationToken(Base):
    __tablename__ = "verification_tokens"
    __table_args__ = ({"schema": "authentication"},)

    token_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("authentication.users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="verification_tokens")


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = ({"schema": "authentication"},)

    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("authentication.users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user_agent = Column(Text)
    ip_address = Column(VARCHAR(50))

    user = relationship("User", back_populates="sessions")


class LoginLog(Base):
    __tablename__ = "login_logs"
    __table_args__ = ({"schema": "authentication"},)

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("authentication.users.user_id"))
    login_time = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(VARCHAR(50))
    user_agent = Column(Text)
    success = Column(Boolean)
    provider_id = Column(
        Integer, ForeignKey("authentication.providers.provider_id")
    )


class Provider(Base):
    __tablename__ = "providers"
    __table_args__ = ({"schema": "authentication"},)

    provider_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # social_authentications = relationship("SocialAuthentication", back_populates="provider")


class Gender(Base):
    __tablename__ = "gender"
    __table_args__ = (
        UniqueConstraint("gender_name", name="gender_idx"),
        {"schema": "global"},
    )

    gender_id = Column(Integer, primary_key=True, index=True)
    gender_name = Column(String(40), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)

    # Relacionamento com 'Person'
    gender_users = relationship("Person", back_populates="gender")


class ContactTypeEnum:
    EMAIL = "Email"
    PHONE = "Telefone"


# class SocialAuthentication(Base):
#     __tablename__ = "social_authentications"
#     __table_args__ = {"schema": "authentication"}

#     social_auth_id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("authentication.users.user_id"), nullable=False)
#     provider_id = Column(Integer, ForeignKey("authentication.providers.provider_id"), nullable=False)
#     access_token = Column(Text, nullable=False)
#     refresh_token = Column(Text, nullable=True)
#     token_expires_at = Column(DateTime, nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

#     user = relationship("User", back_populates="social_authentications")
#     provider = relationship("Provider", back_populates="social_authentications")
