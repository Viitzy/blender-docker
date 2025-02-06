import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool
from google.cloud.sql.connector import Connector, IPTypes
import pg8000.native
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager, asynccontextmanager
from typing import Generator

DATABASE_URL = "postgresql+pg8000://"

connectors = {
    "account": Connector(ip_type=IPTypes.PUBLIC),
    "crawlers": Connector(ip_type=IPTypes.PUBLIC),
    "properties": Connector(ip_type=IPTypes.PUBLIC),
    "real_estate": Connector(ip_type=IPTypes.PUBLIC),
}


def close_connectors():
    for name, connector in connectors.items():
        connector.close()


import atexit

atexit.register(close_connectors)


# Conexão Account
def get_connection_account():
    conn = connectors["account"].connect(
        os.getenv("GCP_CLOUD_SQL_INSTANCE"),
        "pg8000",
        user=os.getenv("GCP_CLOUD_SQL_USER_ACCOUNT"),
        password=os.getenv("GCP_CLOUD_SQL_PS_ACCOUNT"),
        db=os.getenv("GCP_CLOUD_SQL_DB_ACCOUNT"),
    )
    return conn


engine_account = create_engine(
    DATABASE_URL, creator=get_connection_account, poolclass=QueuePool
)
Base = declarative_base()
SessionLocalAccount = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_account
)


# Conexão Real Estate
def get_connection_real_estate():
    conn = connectors["real_estate"].connect(
        os.getenv("GCP_CLOUD_SQL_INSTANCE"),
        "pg8000",
        user=os.getenv("GCP_CLOUD_SQL_USER_REAL_ESTATE"),
        password=os.getenv("GCP_CLOUD_SQL_PS_REAL_ESTATE"),
        db=os.getenv("GCP_CLOUD_SQL_DB_REAL_ESTATE"),
    )
    return conn


engine_real_estate = create_engine(
    DATABASE_URL, creator=get_connection_real_estate, poolclass=QueuePool
)
Base = declarative_base()
SessionLocalRealEstate = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_real_estate
)


# Conexão Crawlers
def get_connection_crawlers():
    conn = connectors["crawlers"].connect(
        os.getenv("GCP_CLOUD_SQL_INSTANCE"),
        "pg8000",
        user=os.getenv("GCP_CLOUD_SQL_USER_CRAWLERS"),
        password=os.getenv("GCP_CLOUD_SQL_PS_CRAWLERS"),
        db=os.getenv("GCP_CLOUD_SQL_DB"),
    )
    return conn


engine_crawlers = create_engine(
    DATABASE_URL, creator=get_connection_crawlers, poolclass=QueuePool
)
Base = declarative_base()
SessionLocalCrawlers = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_crawlers
)


# Conexão Properties
def get_connection_properties():
    conn = connectors["properties"].connect(
        os.getenv("GCP_CLOUD_SQL_INSTANCE"),
        "pg8000",
        user=os.getenv("GCP_CLOUD_SQL_USER_PROPERTIES"),
        password=os.getenv("GCP_CLOUD_SQL_PS_PROPERTIES"),
        db=os.getenv("GCP_CLOUD_SQL_DB_PROPERTIES"),
    )
    return conn


engine_properties = create_engine(
    DATABASE_URL, creator=get_connection_properties, poolclass=QueuePool
)
Base = declarative_base()
SessionLocalProperties = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_properties
)


@contextmanager
def get_connection_account() -> Generator:
    conn = psycopg2.connect(
        dbname=os.getenv("GCP_CLOUD_SQL_DB_ACCOUNT"),
        user=os.getenv("GCP_CLOUD_SQL_USER_ACCOUNT"),
        password=os.getenv("GCP_CLOUD_SQL_PS_ACCOUNT"),
        host=os.getenv("GCP_CLOUD_SQL_DB_HOST"),
        port=os.getenv("GCP_CLOUD_SQL_DB_PORT"),
        cursor_factory=RealDictCursor,
    )
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_connection_auth() -> Generator:
    conn = psycopg2.connect(
        dbname=os.getenv("GCP_CLOUD_SQL_DB_AUTH"),
        user=os.getenv("GCP_CLOUD_SQL_USER_AUTH"),
        password=os.getenv("GCP_CLOUD_SQL_PS_AUTH"),
        host=os.getenv("GCP_CLOUD_SQL_DB_HOST"),
        port=os.getenv("GCP_CLOUD_SQL_DB_PORT"),
        cursor_factory=RealDictCursor,
    )
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_connection_bigfive() -> Generator:
    conn = psycopg2.connect(
        dbname=os.getenv("GCP_CLOUD_SQL_DB_BIGFIVE"),
        user=os.getenv("GCP_CLOUD_SQL_USER_BIGFIVE"),
        password=os.getenv("GCP_CLOUD_SQL_PS_BIGFIVE"),
        host=os.getenv("GCP_CLOUD_SQL_DB_HOST"),
        port=os.getenv("GCP_CLOUD_SQL_DB_PORT"),
        cursor_factory=RealDictCursor,
    )
    try:
        yield conn
    finally:
        conn.close()
