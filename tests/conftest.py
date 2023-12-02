from typing import List

import psycopg2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app import get_app
from common import ObjRef
from logic.customers import Customer
from session.connection import Base
from settings import DatabaseSettings, AppSettings


@pytest.fixture
def db_settings():
    return DatabaseSettings()


class PrefixTestClient(TestClient):
    def __init__(self, starlette_app, prefix, **kwargs):
        super().__init__(starlette_app, **kwargs)
        self.__prefix = prefix

    def request(self, method, url, **kwargs):
        return super().request(method, self.__prefix + url, **kwargs)


@pytest.fixture
def app_settings():
    return AppSettings()


@pytest.fixture
def db_test_settings():
    return DatabaseSettings(db_url_prefix="postgresql")


@pytest.fixture
def db_session_tests(db_test_settings):
    database_url = URL.create(
        drivername=db_test_settings.db_url_prefix,
        username=db_test_settings.db_username,
        password=db_test_settings.db_password,
        host=db_test_settings.db_hostname,
        port=db_test_settings.db_port,
        database=db_test_settings.db_name,
    )
    engine = create_engine(database_url)
    with Session(engine) as session:
        yield session
    session.close()


@pytest.fixture
def client(
    app_settings,
    db_settings,
    db_session_tests
) -> TestClient:

    async def lifespan(application: FastAPI):
        yield

    app = get_app(app_settings, lifespan)
    with PrefixTestClient(app, app_settings.path_prefix) as client:
        # Default customer for most unit tests
        yield client

    # Reset overrides
    app.dependency_overrides = {}
    tables = Base.metadata.tables
    db_session_tests.begin()
    with db_session_tests.connection() as conn:
        # disable foreign keys
        conn.execute(text("BEGIN TRANSACTION;"))
        for table in tables:
            try:
                conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            except ProgrammingError as e:
                print(e)
        conn.execute(text("END TRANSACTION;"))


@pytest.fixture
def customers_example(client) -> List[Customer]:

    customer = Customer(name="Customer A")
    res = client.post("/customers", data=customer.json())
    customer_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/customers/{customer_id}")
    customer_a = Customer.parse_raw(get_res.content)

    customer = Customer(name="Customer B")
    res = client.post("/customers", data=customer.json())
    customer_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/customers/{customer_id}")
    customer_b = Customer.parse_raw(get_res.content)

    customer = Customer(name="Customer C")
    res = client.post("/customers", data=customer.json())
    customer_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/customers/{customer_id}")
    customer_c = Customer.parse_raw(get_res.content)

    return [customer_a, customer_b, customer_c]
