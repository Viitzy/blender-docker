from psycopg2.pool import SimpleConnectionPool
import os
import psycopg2.extras


def get_db_config_account():
    if os.getenv("ENVIRONMENT") == "production":
        return {
            "dbname": os.getenv("GCP_CLOUD_SQL_DB_ACCOUNT"),
            "user": os.getenv("GCP_CLOUD_SQL_USER_ACCOUNT"),
            "password": os.getenv("GCP_CLOUD_SQL_PS_ACCOUNT"),
            "host": "/cloudsql/" + os.getenv("GCP_CLOUD_SQL_INSTANCE"),
            "cursor_factory": psycopg2.extras.DictCursor,
        }

    return {
        "dbname": os.getenv("GCP_CLOUD_SQL_DB_ACCOUNT"),
        "user": os.getenv("GCP_CLOUD_SQL_USER_ACCOUNT"),
        "password": os.getenv("GCP_CLOUD_SQL_PS_ACCOUNT"),
        "host": os.getenv("GCP_CLOUD_SQL_DB_HOST"),
        "port": os.getenv("GCP_CLOUD_SQL_DB_PORT"),
        "cursor_factory": psycopg2.extras.DictCursor,
    }


def get_db_config_auth():
    if os.getenv("ENVIRONMENT") == "production":
        # Production configuration using Cloud SQL Auth Proxy
        return {
            "dbname": os.getenv("GCP_CLOUD_SQL_DB_AUTH"),
            "user": os.getenv("GCP_CLOUD_SQL_USER_AUTH"),
            "password": os.getenv("GCP_CLOUD_SQL_PS_AUTH"),
            "host": "/cloudsql/" + os.getenv("GCP_CLOUD_SQL_INSTANCE"),
            "cursor_factory": psycopg2.extras.DictCursor,
        }
    else:
        # Development configuration
        return {
            "dbname": os.getenv("GCP_CLOUD_SQL_DB_AUTH"),
            "user": os.getenv("GCP_CLOUD_SQL_USER_AUTH"),
            "password": os.getenv("GCP_CLOUD_SQL_PS_AUTH"),
            "host": os.getenv("GCP_CLOUD_SQL_DB_HOST"),
            "port": os.getenv("GCP_CLOUD_SQL_DB_PORT"),
            "cursor_factory": psycopg2.extras.DictCursor,
        }


def get_db_config_bigfive():
    if os.getenv("ENVIRONMENT") == "production":
        # Production configuration using Cloud SQL Auth Proxy
        return {
            "dbname": os.getenv("GCP_CLOUD_SQL_DB_BIGFIVE"),
            "user": os.getenv("GCP_CLOUD_SQL_USER_BIGFIVE"),
            "password": os.getenv("GCP_CLOUD_SQL_PS_BIGFIVE"),
            "host": "/cloudsql/" + os.getenv("GCP_CLOUD_SQL_INSTANCE"),
            "cursor_factory": psycopg2.extras.DictCursor,
        }
    else:
        # Development configuration
        return {
            "dbname": os.getenv("GCP_CLOUD_SQL_DB_BIGFIVE"),
            "user": os.getenv("GCP_CLOUD_SQL_USER_BIGFIVE"),
            "password": os.getenv("GCP_CLOUD_SQL_PS_BIGFIVE"),
            "host": os.getenv("GCP_CLOUD_SQL_DB_HOST"),
            "port": os.getenv("GCP_CLOUD_SQL_DB_PORT"),
            "cursor_factory": psycopg2.extras.DictCursor,
        }


def get_db_config_real_estate():
    return {
        "dbname": os.getenv("GCP_CLOUD_SQL_DB_REAL_ESTATE"),
        "user": os.getenv("GCP_CLOUD_SQL_USER_REAL_ESTATE"),
        "password": os.getenv("GCP_CLOUD_SQL_PS_REAL_ESTATE"),
        "host": os.getenv("GCP_CLOUD_SQL_DB_HOST"),
        "port": os.getenv("GCP_CLOUD_SQL_DB_PORT"),
        "cursor_factory": psycopg2.extras.DictCursor,
    }


# Connection pool configuration
def get_pool_account():
    return SimpleConnectionPool(
        minconn=1, maxconn=20, **get_db_config_account()
    )


def get_pool_auth():
    return SimpleConnectionPool(minconn=1, maxconn=20, **get_db_config_auth())


def get_pool_bigfive():
    return SimpleConnectionPool(
        minconn=1, maxconn=20, **get_db_config_bigfive()
    )


def get_pool_real_estate():
    return SimpleConnectionPool(
        minconn=1, maxconn=20, **get_db_config_real_estate()
    )


def get_conn_account():
    pool = get_pool_account()
    return pool, pool.getconn()


def get_conn_auth():
    pool = get_pool_auth()
    return pool, pool.getconn()


def put_conn_account(pool, conn):
    pool.putconn(conn)


def put_conn_auth(pool, conn):
    pool.putconn(conn)


def get_conn_bigfive():
    pool = get_pool_bigfive()
    return pool, pool.getconn()


def put_conn_bigfive(pool, conn):
    pool.putconn(conn)


def get_conn_real_estate():
    pool = get_pool_real_estate()
    return pool, pool.getconn()


def put_conn_real_estate(pool, conn):
    pool.putconn(conn)
