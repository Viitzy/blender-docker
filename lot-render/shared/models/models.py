from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    CHAR,
    ForeignKey,
    Float,
    Date,
    Boolean,
    Text,
    DateTime,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship, backref
from shared.database.connections import Base
from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Numeric,
    Boolean,
    ForeignKey,
    Sequence,
    UniqueConstraint,
    JSON,
)
from datetime import datetime


# Architect Model
class Architect(Base):
    __tablename__ = "architect"
    __table_args__ = (
        UniqueConstraint("architect_name", name="architect_name_idx"),
        {"schema": "properties"},
    )

    architect_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "architect_seq", schema="properties"
        ).next_value(),
    )
    architect_name = Column(String(150), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Companies Model
class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("company_name", name="company_name_idx"),
        {"schema": "properties"},  # Combina os constraints e o schema
    )

    company_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "companies_seq", schema="properties"
        ).next_value(),
    )
    company_name = Column(String(255), nullable=False)
    company_type_id = Column(
        Integer,
        ForeignKey("properties.company_types.company_type_id"),
        nullable=False,
    )
    cnpj = Column(String(14))
    address_id = Column(
        Integer, ForeignKey("global.addresses.address_id"), nullable=False
    )
    website = Column(String(255))
    href = Column(String(200))
    creci = Column(String(30))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Company Contacts Model
class CompanyContact(Base):
    __tablename__ = "company_contacts"
    __table_args__ = (
        UniqueConstraint("contact_value", name="contact_value_idx"),
        {"schema": "properties"},
    )

    company_contact_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "company_contacts_seq", schema="properties"
        ).next_value(),
    )
    company_id = Column(
        Integer, ForeignKey("properties.companies.company_id"), nullable=False
    )
    contact_type_id = Column(
        Integer,
        ForeignKey("global.contact_types.contact_type_id"),
        nullable=False,
    )
    contact_value = Column(String(250))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Company Types Model
class CompanyType(Base):
    __tablename__ = "company_types"
    __table_args__ = (
        UniqueConstraint("company_type_name", name="company_type_name_idx"),
        {"schema": "properties"},  # Combina os constraints e o schema
    )

    company_type_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "company_types_seq", schema="properties"
        ).next_value(),
    )
    company_type_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Seller Type Model
class SellerType(Base):
    __tablename__ = "seller_type"
    __table_args__ = (
        UniqueConstraint(
            "seller_type_name", name="seller_type_seq_idx"
        ),  # Constraint
        {"schema": "properties"},  # Define o schema explicitamente
    )

    seller_type_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "seller_type_seq", schema="properties"
        ).next_value(),
    )
    seller_type_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Company User Model
class CompanyUser(Base):
    __tablename__ = "company_users"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "user_id", "seller_type_id", name="company_users_idx1"
        ),  # Constraint
        {"schema": "properties"},  # Define o schema explicitamente
    )

    company_users_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "company_users_seq", schema="properties"
        ).next_value(),
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
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)

    # Relacionamento com a tabela `User`
    user = relationship("User", back_populates="company_users")


# Lot Sellers Model
class LotSellers(Base):
    __tablename__ = "lot_sellers"
    __table_args__ = (
        UniqueConstraint(
            "lot_id", "user_id", "seller_type_id", name="lot_sellers_idx1"
        ),
        {"schema": "properties"},
    )

    lot_sellers_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_sellers_seq", schema="properties"
        ).next_value(),
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
    )  # Certifique-se de que o schema está correto
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    company_reference = Column(String(20))


# Component Model
class Component(Base):
    __tablename__ = "component"
    __table_args__ = (
        UniqueConstraint("component_name", name="component_name_idx"),
        {"schema": "properties"},
    )

    component_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "component_seq", schema="properties"
        ).next_value(),
    )
    component_name = Column(String(150), nullable=False)
    component_type_id = Column(
        Integer,
        ForeignKey("properties.component_type.component_type_id"),
        nullable=False,
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Component Price Model
class ComponentPrice(Base):
    __tablename__ = "component_price"
    __table_args__ = {"schema": "properties"}

    component_price_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "component_price_seq", schema="properties"
        ).next_value(),
    )
    component_version_id = Column(
        Integer,
        ForeignKey("properties.component_version.component_version_id"),
        nullable=False,
    )
    city_id = Column(Integer, ForeignKey("global.cities.city_id"))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Component Type Model
class ComponentType(Base):
    __tablename__ = "component_type"
    __table_args__ = (
        UniqueConstraint("component_type_name", name="component_type_name_idx"),
        {"schema": "properties"},
    )

    component_type_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "component_type_seq", schema="properties"
        ).next_value(),
    )
    component_type_name = Column(String(150), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Component Version Model
class ComponentVersion(Base):
    __tablename__ = "component_version"
    __table_args__ = (
        UniqueConstraint(
            "component_id",
            "version",
            name="component_version_comp_id_version_idx",
        ),
        {"schema": "properties"},
    )

    component_version_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "component_version_seq", schema="properties"
        ).next_value(),
    )
    component_id = Column(
        Integer, ForeignKey("properties.component.component_id"), nullable=False
    )
    version = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


class ProjectVersionLots(Base):
    __tablename__ = "project_version_lots"
    __table_args__ = (
        UniqueConstraint(
            "project_version_id", "lot_id", name="project_version_lots_idx"
        ),
        {"schema": "properties"},
    )

    project_version_lots_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "project_version_lots_seq", schema="properties"
        ).next_value(),
        nullable=False,
    )
    project_version_id = Column(
        Integer,
        ForeignKey(
            "properties.project_version.project_version_id",
            name="fk_pvl_project_version",
        ),
        nullable=False,
    )
    lot_id = Column(
        Integer,
        ForeignKey("properties.lots.lot_id", name="fk_pvl_lots"),
        nullable=False,
    )
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)

    # Relacionamentos
    project_version = relationship(
        "ProjectVersion", back_populates="project_version_lots"
    )
    lot = relationship("Lot", back_populates="project_version_lots")


# Environment Model
class Environment(Base):
    __tablename__ = "environment"
    __table_args__ = (
        UniqueConstraint("environment_name", name="environment_name_idx"),
        {"schema": "properties"},
    )

    environment_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "environment_seq", schema="properties"
        ).next_value(),
    )
    environment_name = Column(String(150), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Environment Detail Model
class EnvironmentDetail(Base):
    __tablename__ = "environment_detail"
    __table_args__ = (
        UniqueConstraint(
            "environment_version_id",
            "room_version_id",
            name="environment_detail_env_version_room_version_id_idx",
        ),
        {"schema": "properties"},
    )

    environment_detail_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "environment_detail_seq", schema="properties"
        ).next_value(),
    )
    environment_version_id = Column(
        Integer,
        ForeignKey("properties.environment_version.environment_version_id"),
        nullable=False,
    )
    room_version_id = Column(
        Integer,
        ForeignKey("properties.room_version.room_version_id"),
        nullable=False,
    )
    ordem = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Environment Version Model
class EnvironmentVersion(Base):
    __tablename__ = "environment_version"
    __table_args__ = (
        UniqueConstraint(
            "environment_id",
            "version",
            name="environment_version_env_id_version_idx",
        ),
        {"schema": "properties"},
    )

    environment_version_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "environment_version_seq", schema="properties"
        ).next_value(),
    )
    environment_id = Column(
        Integer,
        ForeignKey("properties.environment.environment_id"),
        nullable=False,
    )
    version = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Lot Address History Model
class LotAddressHistory(Base):
    __tablename__ = "lot_address_history"
    __table_args__ = {"schema": "properties"}

    lot_address_history_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_address_history_seq", schema="properties"
        ).next_value(),
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )  # Adicionar o schema correto
    address_id = Column(
        Integer, ForeignKey("global.addresses.address_id"), nullable=False
    )
    modified_by_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Lot Address Request Status Model
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
        primary_key=True,
        server_default=Sequence(
            "lot_address_request_status_seq", schema="properties"
        ).next_value(),
    )
    lot_address_request_status_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Lot Address Request Status History Model
class LotAddressRequestStatusHistory(Base):
    __tablename__ = "lot_address_request_status_history"
    __table_args__ = {"schema": "properties"}

    lot_address_request_status_history_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_address_request_status_history_seq", schema="properties"
        ).next_value(),
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
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Lot Address Request Users Model
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

    lot_address_request_users = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_address_request_users_seq", schema="properties"
        ).next_value(),
    )
    lot_address_requests_id = Column(
        Integer,
        ForeignKey("properties.lot_address_requests.lot_address_requests_id"),
        nullable=False,
    )
    user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Lot Address Requests Model
class LotAddressRequests(Base):
    __tablename__ = "lot_address_requests"
    __table_args__ = {"schema": "properties"}

    lot_address_requests_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_address_requests_seq", schema="properties"
        ).next_value(),
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    address_id = Column(Integer, ForeignKey("global.addresses.address_id"))
    responsible_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id")
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Lot Area History Model
class LotAreaHistory(Base):
    __tablename__ = "lot_area_history"
    __table_args__ = {"schema": "properties"}

    lot_area_history_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_area_history_seq", schema="properties"
        ).next_value(),
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    area = Column(Numeric(10, 2), nullable=False)
    modified_by_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Lot Price History Model
class LotPriceHistory(Base):
    __tablename__ = "lot_price_history"
    __table_args__ = {"schema": "properties"}

    lot_price_history_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_price_history_seq", schema="properties"
        ).next_value(),
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    price = Column(Numeric(10, 2), nullable=False)
    modified_by_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Lot Status Model
class LotStatus(Base):
    __tablename__ = "lot_status"
    __table_args__ = (
        UniqueConstraint("lot_status_name", name="lot_status_name_idx"),
        {"schema": "properties"},
    )

    lot_status_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_status_seq", schema="properties"
        ).next_value(),
    )
    lot_status_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Lot Status History Model
class LotStatusHistory(Base):
    __tablename__ = "lot_status_history"
    __table_args__ = {"schema": "properties"}

    lot_status_history_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_status_history_seq", schema="properties"
        ).next_value(),
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
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Lot Visit Status History Model
class LotVisitStatusHistory(Base):
    __tablename__ = "lot_visit_status_history"
    __table_args__ = (
        UniqueConstraint(
            "lot_visit_id",
            "visit_status_id",
            name="lot_visit_status_history_idx",
        ),
        {"schema": "properties"},
    )

    lot_visit_status_history_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_visit_status_history_seq", schema="properties"
        ).next_value(),
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
    visit_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    suggested_visit_dates = Column(JSON)


# Lot Visits Model
class LotVisits(Base):
    __tablename__ = "lot_visits"
    __table_args__ = {"schema": "properties"}

    lot_visit_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "lot_visits_seq", schema="properties"
        ).next_value(),
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("authentication.users.user_id"), nullable=False
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    responsible_user_id = Column(
        Integer, ForeignKey("authentication.users.user_id")
    )


# Lots Model
class Lot(Base):
    __tablename__ = "lots"
    __table_args__ = {"schema": "properties"}

    lot_id = Column(Integer, primary_key=True, index=True)
    region_id = Column(
        Integer, ForeignKey("global.regions.region_id"), nullable=False
    )
    title = Column(String(255), nullable=False)
    link = Column(String(255))
    condominium_fee = Column(Numeric(10, 2))
    viva_real_code = Column(String(255))
    processed = Column(CHAR, default="N", nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP)
    address_id = Column(
        Integer, ForeignKey("global.addresses.address_id"), nullable=False
    )
    latitude = Column(Numeric)  # Latitude do lote
    longitude = Column(Numeric)  # Longitude do lote
    latitude_adjusted = Column(Numeric)  # Latitude ajustada
    longitude_adjusted = Column(Numeric)  # Longitude ajustada

    # Relacionamento com Address
    address = relationship("Address", back_populates="lots")

    # Relacionamento com Region
    region = relationship("Region")
    project_version_lots = relationship(
        "ProjectVersionLots", back_populates="lot"
    )


# Project Model
class Project(Base):
    __tablename__ = "project"
    __table_args__ = {"schema": "properties"}  # Defina o esquema correto aqui

    project_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "project_seq", schema="properties"
        ).next_value(),
    )
    project_name = Column(String(150), nullable=False)
    architect_id = Column(
        Integer, ForeignKey("properties.architect.architect_id"), nullable=False
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Definir relacionamento, se necessário
    architect = relationship("Architect", backref="projects")


# Project Detail Model
class ProjectDetail(Base):
    __tablename__ = "project_detail"
    __table_args__ = (
        UniqueConstraint(
            "project_version_id",
            "environment_version_id",
            name="project_detail_pro_ver_id_env_ver_id_idx",
        ),
        {"schema": "properties"},
    )

    project_detail_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "project_detail_seq", schema="properties"
        ).next_value(),
    )
    project_version_id = Column(
        Integer,
        ForeignKey("properties.project_version.project_version_id"),
        nullable=False,
    )
    environment_version_id = Column(
        Integer,
        ForeignKey("properties.environment_version.environment_version_id"),
        nullable=False,
    )
    ordem = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Project Version Model
class ProjectVersion(Base):
    __tablename__ = "project_version"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "version",
            name="project_version_project_id_version_idx",
        ),
        {"schema": "properties"},
    )

    project_version_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "project_version_seq", schema="properties"
        ).next_value(),
    )
    project_id = Column(
        Integer, ForeignKey("properties.project.project_id"), nullable=False
    )
    version = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)

    # Adicione este relacionamento
    images = relationship(
        "ProjectVersionImage", back_populates="project_version", lazy="joined"
    )

    # Outros relacionamentos
    project_version_lots = relationship(
        "ProjectVersionLots", back_populates="project_version"
    )


class ProjectVersionImage(Base):
    __tablename__ = "project_version_images"
    __table_args__ = {"schema": "properties"}

    project_version_image_id = Column(Integer, primary_key=True)
    project_version_id = Column(
        Integer,
        ForeignKey("properties.project_version.project_version_id"),
        nullable=False,
    )
    project_version_image_url = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)

    # Relacionamento com ProjectVersion
    project_version = relationship("ProjectVersion", back_populates="images")


# Room Model
class Room(Base):
    __tablename__ = "room"
    __table_args__ = {"schema": "properties"}

    room_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence("room_seq", schema="properties").next_value(),
    )
    room_name = Column(String(150), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Room Styles Model
class RoomStyle(Base):
    __tablename__ = "room_styles"
    __table_args__ = (
        UniqueConstraint(
            "room_version_id",
            "style_version_id",
            name="room_styles_room_ver_id_sty_ver_idx",
        ),
        {"schema": "properties"},
    )

    room_style_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "room_styles_seq", schema="properties"
        ).next_value(),
    )
    room_version_id = Column(
        Integer,
        ForeignKey("properties.room_version.room_version_id"),
        nullable=False,
    )
    style_version_id = Column(
        Integer,
        ForeignKey("properties.style_version.style_version_id"),
        nullable=False,
    )
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Room Version Model
class RoomVersion(Base):
    __tablename__ = "room_version"
    __table_args__ = (
        UniqueConstraint(
            "room_id", "version", name="room_version_room_id_version_idx"
        ),
        {"schema": "properties"},
    )

    room_version_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "room_version_seq", schema="properties"
        ).next_value(),
    )
    room_id = Column(
        Integer, ForeignKey("properties.room.room_id"), nullable=False
    )
    version = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
    room_size = Column(Numeric(10, 2))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Style Model
class Style(Base):
    __tablename__ = "style"
    __table_args__ = (
        UniqueConstraint("style_name", name="style_name_idx"),
        {"schema": "properties"},
    )

    style_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence("style_seq", schema="properties").next_value(),
    )
    style_name = Column(String(150), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Style Detail Model
class StyleDetail(Base):
    __tablename__ = "style_detail"
    __table_args__ = (
        UniqueConstraint(
            "style_version_id",
            "component_version_id",
            name="style_detail__st_version_comp_version_idx",
        ),
        {"schema": "properties"},
    )

    style_detail_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "style_detail_seq", schema="properties"
        ).next_value(),
    )
    style_version_id = Column(
        Integer,
        ForeignKey("properties.style_version.style_version_id"),
        nullable=False,
    )
    component_version_id = Column(
        Integer,
        ForeignKey("properties.component_version.component_version_id"),
        nullable=False,
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Style Version Model
class StyleVersion(Base):
    __tablename__ = "style_version"
    __table_args__ = (
        UniqueConstraint(
            "style_id", "version", name="style_version_style_id_version_idx"
        ),
        {"schema": "properties"},
    )

    style_version_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "style_version_seq", schema="properties"
        ).next_value(),
    )
    style_id = Column(
        Integer, ForeignKey("properties.style.style_id"), nullable=False
    )
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


# Visit Status Model
class VisitStatus(Base):
    __tablename__ = "visit_status"
    __table_args__ = (
        UniqueConstraint("visit_status_name", name="visit_status_name_idx"),
        {"schema": "properties"},
    )

    visit_status_id = Column(
        Integer,
        primary_key=True,
        server_default=Sequence(
            "visit_status_seq", schema="properties"
        ).next_value(),
    )
    visit_status_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = {"schema": "global"}

    address_id = Column(Integer, primary_key=True, index=True)
    street = Column(String(255), nullable=False)
    number = Column(Integer)
    complement = Column(String(255))
    neighborhood = Column(String(255))
    city_id = Column(
        Integer, ForeignKey("global.cities.city_id"), nullable=False
    )
    postal_code = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, onupdate=func.now())

    # Relacionamento com City
    city = relationship("City", back_populates="addresses")

    # Relacionamento com Lot - Aqui está o ponto crítico!
    lots = relationship("Lot", back_populates="address")


class City(Base):
    __tablename__ = "cities"
    __table_args__ = {"schema": "global"}

    city_id = Column(Integer, primary_key=True, index=True)
    city_name = Column(String(255), nullable=False)
    state_id = Column(
        Integer, ForeignKey("global.states.state_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, onupdate=func.now())

    # Relationship with State and Address
    state = relationship("State", back_populates="cities")
    addresses = relationship("Address", back_populates="city")


class State(Base):
    __tablename__ = "states"
    __table_args__ = {"schema": "global"}

    state_id = Column(Integer, primary_key=True, index=True)
    state_name = Column(String(100), nullable=False)
    country_id = Column(
        Integer, ForeignKey("global.countries.country_id"), nullable=False
    )
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, onupdate=func.now())

    # Relationship with Country and City
    country = relationship("Country", back_populates="states")
    cities = relationship("City", back_populates="state")


class Country(Base):
    __tablename__ = "countries"
    __table_args__ = {"schema": "global"}

    country_id = Column(Integer, primary_key=True, index=True)
    country_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, onupdate=func.now())

    # Relationship with states
    states = relationship("State", back_populates="country")


class RegionType(Base):
    __tablename__ = "region_types"
    __table_args__ = {"schema": "global"}

    region_type_id = Column(Integer, primary_key=True, index=True)
    region_type_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, onupdate=func.now())

    # Relationship with regions
    regions = relationship("Region", back_populates="region_type")


class Region(Base):
    __tablename__ = "regions"
    __table_args__ = {"schema": "global"}

    region_id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String(255), nullable=False)
    region_type_id = Column(
        Integer,
        ForeignKey("global.region_types.region_type_id"),
        nullable=False,
    )
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, onupdate=func.now())

    # Relationship with region types
    region_type = relationship("RegionType", back_populates="regions")

    images = relationship("RegionImage", back_populates="region")


####A SER VALIDADO ABAIXO#####


class Person(Base):
    __tablename__ = "people"
    __table_args__ = {"schema": "global"}

    person_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    # Relacionamento com User (definido aqui com back_populates)
    user = relationship("User", back_populates="person")


class PersonContact(Base):
    __tablename__ = "person_contacts"
    __table_args__ = {"schema": "global"}

    person_contact_id = Column(Integer, primary_key=True)
    contact_type_id = Column(
        Integer, ForeignKey("global.contact_types.contact_type_id")
    )

    # Definir o relacionamento com ContactType
    contact_type = relationship("ContactType", back_populates="person_contacts")


class ContactType(Base):
    __tablename__ = "contact_types"
    __table_args__ = {"schema": "global"}

    contact_type_id = Column(Integer, primary_key=True)
    contact_type_name = Column(String(50), nullable=False, unique=True)

    # Relacionamento com PersonContact
    person_contacts = relationship(
        "PersonContact", back_populates="contact_type"
    )


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
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)

    # Relacionamento com a tabela `CompanyUser`
    company_users = relationship("CompanyUser", back_populates="user")

    # Relacionamento com a tabela `Person` (já corrigido)
    person = relationship("Person", back_populates="user")
    # lot_seller = relationship("LotSeller", back_populates="user")


# class RegionImage(Base):
#     __tablename__ = "region_images"
#     __table_args__ = {"schema": "global"}

#     region_images_id = Column(
#         Integer, primary_key=True, index=True, autoincrement=True
#     )
#     region_id = Column(
#         Integer, ForeignKey("global.regions.region_id"), nullable=False
#     )
#     home_image_url = Column(String(255), nullable=False)
#     menu_image_url = Column(String(255), nullable=False)
#     created_at = Column(DateTime, nullable=False)
#     updated_at = Column(DateTime, nullable=True)

#     # Relacionamento com Region
#     region = relationship("Region", back_populates="images")


class ReferencePoint(Base):
    __tablename__ = "reference_points"

    reference_point_id = Column(Integer, primary_key=True)
    reference_point_name = Column(String(200), nullable=False)
    latitude = Column(Numeric, nullable=False)
    longitude = Column(Numeric, nullable=False)
    address_id = Column(
        Integer, ForeignKey("global.addresses.address_id"), nullable=False
    )
    nota = Column(Numeric, nullable=True)
    user_rating_counts = Column(
        Integer, nullable=True
    )  # Adicionado o campo user_ratings_count
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "reference_point_name", name="reference_points_name_idx"
        ),
        {"schema": "properties"},
    )


class ReferencePointType(Base):
    __tablename__ = "reference_point_type"

    reference_point_type_id = Column(Integer, primary_key=True)
    reference_point_type_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "reference_point_type_name", name="reference_point_type_name_idx"
        ),
        {"schema": "properties"},
    )


class ReferencePointAssignment(Base):
    __tablename__ = "reference_point_assignments"

    reference_point_assignment_id = Column(Integer, primary_key=True)
    reference_point_id = Column(
        Integer,
        ForeignKey("properties.reference_points.reference_point_id"),
        nullable=False,
    )
    reference_point_type_id = Column(
        Integer,
        ForeignKey("properties.reference_point_type.reference_point_type_id"),
        nullable=False,
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "reference_point_id",
            "reference_point_type_id",
            name="reference_pouint_id_type_idx",
        ),
        {"schema": "properties"},
    )


class ReferencePointLot(Base):
    __tablename__ = "reference_points_lot"

    reference_points_lot_id = Column(Integer, primary_key=True)
    reference_point_id = Column(
        Integer,
        ForeignKey("properties.reference_points.reference_point_id"),
        nullable=False,
    )
    lot_id = Column(
        Integer, ForeignKey("properties.lots.lot_id"), nullable=False
    )
    distance = Column(Numeric, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "reference_point_id",
            "lot_id",
            name="reference_points_lot_rp_li_idx",
        ),
        {"schema": "properties"},
    )


class ReferencePointRegion(Base):
    __tablename__ = "reference_points_region"

    reference_points_region_id = Column(Integer, primary_key=True)
    reference_point_id = Column(
        Integer,
        ForeignKey("properties.reference_points.reference_point_id"),
        nullable=False,
    )
    region_id = Column(
        Integer, ForeignKey("global.regions.region_id"), nullable=False
    )
    distance = Column(Numeric, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "reference_point_id",
            "region_id",
            name="reference_points_region_rp_reg",
        ),
        {"schema": "properties"},
    )


class Page(Base):
    __tablename__ = "pages"
    # __table_args__ = {"schema": "properties"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    contents = relationship("PageContent", back_populates="page")


class PageContent(Base):
    __tablename__ = "page_contents"
    # __table_args__ = {"schema": "properties"}

    id = Column(Integer, primary_key=True, index=True)
    # page_id = Column(Integer, ForeignKey("properties.pages.id"))
    page_id = Column(Integer, ForeignKey("pages.id"))
    section = Column(String, index=True)
    content_type = Column(String, index=True)
    content = Column(Text)
    page = relationship("Page", back_populates="contents")
