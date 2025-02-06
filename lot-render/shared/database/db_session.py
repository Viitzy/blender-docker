from .connections import (
    SessionLocalAccount,
    SessionLocalCrawlers,
    SessionLocalProperties,
    SessionLocalRealEstate,
)
from contextlib import contextmanager
from shared.database.pool import (
    get_conn_account,
    get_conn_auth,
    get_conn_bigfive,
    get_conn_real_estate,
    put_conn_account,
    put_conn_auth,
    put_conn_bigfive,
    put_conn_real_estate,
)
import psycopg2.extras


@contextmanager
def get_db_real_estate():
    pool, conn = get_conn_real_estate()
    try:
        conn.cursor_factory = psycopg2.extras.DictCursor
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            put_conn_real_estate(pool, conn)
        except Exception:
            pass


def get_db_crawlers():
    db = SessionLocalCrawlers()
    try:
        yield db
    finally:
        db.close()


def get_db_properties():
    db = SessionLocalProperties()
    try:
        yield db
    finally:
        db.close()


def get_db_account():
    pool, conn = get_conn_account()
    try:
        conn.cursor_factory = psycopg2.extras.DictCursor
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            put_conn_account(pool, conn)
        except Exception:
            pass


@contextmanager
def get_db_auth():
    pool, conn = get_conn_auth()
    try:
        conn.cursor_factory = psycopg2.extras.DictCursor
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            put_conn_auth(pool, conn)
        except Exception:
            pass


@contextmanager
def get_db_bigfive():
    pool, conn = get_conn_bigfive()
    try:
        conn.cursor_factory = psycopg2.extras.DictCursor
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            put_conn_bigfive(pool, conn)
        except Exception:
            pass
