from typing import List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import Session

from app import get_app
from enums import AcademicType
from participants.business import Participant, CompanyParticipant, \
    GovernmentOrganismParticipant, AcademicParticipant
from participants.natural_person import NaturalPersonParticipant
from session.connection import Base
from settings import DatabaseSettings, AppSettings
from tests.schemas import ObjRef


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
            conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        conn.execute(text("END TRANSACTION;"))


@pytest.fixture
def example(client) -> List[Participant]:
    participant_creation_data = NaturalPersonParticipant.parse_obj(
        dict(first_name="John Sunday", last_name="Peron", type="NATURAL_PERSON",
             identification=dict(type="DNI", id="37993169")))
    res = client.post("/participants", data=participant_creation_data.json())
    participant_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/participants/{participant_id}")
    natural_person = Participant.parse_raw(get_res.content)

    participant_creation_data = CompanyParticipant(full_name="A company", cuit="20379931694")
    res = client.post("/participants", data=participant_creation_data.json())
    participant_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/participants/{participant_id}")
    company = Participant.parse_raw(get_res.content)

    participant_creation_data = GovernmentOrganismParticipant(full_name="A participant", sector="National")
    res = client.post("/participants", data=participant_creation_data.json())
    participant_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/participants/{participant_id}")
    government_organism = Participant.parse_raw(get_res.content)

    participant_creation_data = AcademicParticipant(full_name="A participant",
                                                    education_level=AcademicType.UNIVERSITY)
    res = client.post("/participants", data=participant_creation_data.json())
    participant_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/participants/{participant_id}")
    academic = Participant.parse_raw(get_res.content)

    return [natural_person, company, government_organism, academic]
