from typing import List

import psycopg2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app import get_app
from logic.accounts import Account
from logic.accounts.business import AddressWithBalance
from logic.participants import Participant, RetrievedNaturalPerson, RetrievedParticipant
from logic.participants import GovernmentOrganismParticipant
from logic.participants import CompanyParticipant
from logic.participants import UniversityParticipant
from logic.participants.natural_person import NaturalPersonParticipant
from logic.recharges.recharge import RetrievedRecharge, RetrievedWaitingRecharge, RetrievedSatisfiedRecharge, \
    RetrievedRejectedRecharge
from session.connection import Base
from settings import DatabaseSettings, AppSettings, AccountsSettings
from common import ObjRef


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
def participant_example(client, natural_person_participant) -> List[RetrievedParticipant]:

    participant_creation_data = CompanyParticipant(full_name="A company", cuit="20379931694")
    res = client.post("/participants", data=participant_creation_data.json())
    participant_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/participants/{participant_id}")
    company = RetrievedParticipant.parse_raw(get_res.content)

    participant_creation_data = GovernmentOrganismParticipant(full_name="A participant", sector="National")
    res = client.post("/participants", data=participant_creation_data.json())
    participant_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/participants/{participant_id}")
    government_organism = RetrievedParticipant.parse_raw(get_res.content)

    participant_creation_data = UniversityParticipant(full_name="A participant")
    res = client.post("/participants", data=participant_creation_data.json())
    participant_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/participants/{participant_id}")
    academic = RetrievedParticipant.parse_raw(get_res.content)

    return [natural_person_participant, company, government_organism, academic]


@pytest.fixture
def recharges_example_from_natural_person(client, address_from_natural_person_participant) -> List[RetrievedRecharge]:

    retrieved_recharge = create_recharge(address_from_natural_person_participant, client)
    retrieved_satisfied_recharge = create_satisfied_recharge(address_from_natural_person_participant, client)
    retrieved_rejected_recharge = create_rejected_recharge(address_from_natural_person_participant, client)
    retrieved_rejected_recharge_2 = create_rejected_recharge(address_from_natural_person_participant, client)

    return [retrieved_recharge, retrieved_satisfied_recharge, retrieved_rejected_recharge, retrieved_rejected_recharge_2]


def create_rejected_recharge(address_from_natural_person_participant, client):
    res_recharges = client.post(f"/accounts/{address_from_natural_person_participant}/recharges")
    recharge_id = ObjRef.parse_raw(res_recharges.content).id
    client.post(f"/recharges/{recharge_id}/reject")
    get_recharge_res = client.get(f"/recharges/{recharge_id}")
    retrieved_rejected_recharge = RetrievedRejectedRecharge.parse_raw(get_recharge_res.content)
    return retrieved_rejected_recharge


def create_satisfied_recharge(address_from_natural_person_participant, client):
    res_recharges = client.post(f"/accounts/{address_from_natural_person_participant}/recharges")
    recharge_id = ObjRef.parse_raw(res_recharges.content).id
    client.post(f"/recharges/{recharge_id}/satisfy")
    get_recharge_res = client.get(f"/recharges/{recharge_id}")
    retrieved_satisfied_recharge = RetrievedSatisfiedRecharge.parse_raw(get_recharge_res.content)
    return retrieved_satisfied_recharge


def create_recharge(address_from_natural_person_participant, client):
    res_recharges = client.post(f"/accounts/{address_from_natural_person_participant}/recharges")
    recharge_id = ObjRef.parse_raw(res_recharges.content).id
    get_recharge_res = client.get(f"/recharges/{recharge_id}")
    retrieved_recharge = RetrievedWaitingRecharge.parse_raw(get_recharge_res.content)
    return retrieved_recharge


@pytest.fixture
def recharges_example_from_natural_person_2(client, address_from_natural_person_participant_2) -> List[RetrievedRecharge]:
    retrieved_recharge = create_recharge(address_from_natural_person_participant_2, client)
    retrieved_satisfied_recharge = create_satisfied_recharge(address_from_natural_person_participant_2, client)
    retrieved_rejected_recharge = create_rejected_recharge(address_from_natural_person_participant_2, client)
    retrieved_rejected_recharge_2 = create_rejected_recharge(address_from_natural_person_participant_2, client)
    return [retrieved_recharge, retrieved_satisfied_recharge, retrieved_rejected_recharge,
            retrieved_rejected_recharge_2]

@pytest.fixture
def recharges_example_2_from_natural_person(client, address_2_from_natural_person_participant) -> List[RetrievedRecharge]:
    retrieved_recharge = create_recharge(address_2_from_natural_person_participant, client)
    retrieved_satisfied_recharge = create_satisfied_recharge(address_2_from_natural_person_participant, client)
    retrieved_rejected_recharge = create_rejected_recharge(address_2_from_natural_person_participant, client)
    retrieved_rejected_recharge_2 = create_rejected_recharge(address_2_from_natural_person_participant, client)
    return [retrieved_recharge, retrieved_satisfied_recharge, retrieved_rejected_recharge,
            retrieved_rejected_recharge_2]


@pytest.fixture
def recharges_example(client, recharges_example_from_natural_person, recharges_example_2_from_natural_person, recharges_example_from_natural_person_2) -> List[RetrievedRecharge]:
    return recharges_example_from_natural_person + recharges_example_2_from_natural_person + recharges_example_from_natural_person_2


@pytest.fixture
def natural_person_participant(client) -> RetrievedParticipant:
    participant_creation_data = NaturalPersonParticipant.parse_obj(
        dict(first_name="John Sunday", last_name="Peron", type="NATURAL_PERSON",
             identification=dict(type="DNI", value="37993169")))
    natural_person = create_participant(client, participant_creation_data)
    return natural_person


def create_participant(client, participant_creation_data):
    res = client.post("/participants", data=participant_creation_data.json())
    participant_id = ObjRef.parse_raw(res.content).id
    get_res = client.get(f"/participants/{participant_id}")
    natural_person = RetrievedParticipant.parse_raw(get_res.content)
    return natural_person


@pytest.fixture
def natural_person_participant_2(client) -> RetrievedParticipant:
    participant_creation_data = NaturalPersonParticipant.parse_obj(
        dict(first_name="Xavier", last_name="Mylaw", type="NATURAL_PERSON",
             identification=dict(type="DNI", value="37993169")))
    natural_person = create_participant(client, participant_creation_data)
    return natural_person


@pytest.fixture
def specific_natural_person_participant(natural_person_participant) -> RetrievedNaturalPerson:
    return natural_person_participant.__root__

@pytest.fixture
def specific_natural_person_participant_2(natural_person_participant_2) -> RetrievedNaturalPerson:
    return natural_person_participant_2.__root__

@pytest.fixture
def account_settings():
    return AccountsSettings()

@pytest.fixture
def balance_limit_per_account(account_settings):
    return account_settings.balance_limit


@pytest.fixture
def address_from_natural_person_participant(client: TestClient, specific_natural_person_participant):
    account_creation = Account.parse_obj({"address": "0x42D429eaB483e88aBa5A80aF056dEC3610886101", "participant_id": specific_natural_person_participant.id, "balance": "0"})
    create_verified_account(account_creation, client, specific_natural_person_participant)
    return account_creation.address



@pytest.fixture
def address_2_from_natural_person_participant(client: TestClient, specific_natural_person_participant):
    account_creation = Account.parse_obj({"address": "0xb794f5ea0ba39494ce839613fffba74279579268", "participant_id": specific_natural_person_participant.id, "balance": "0"})
    create_verified_account(account_creation, client, specific_natural_person_participant)
    return account_creation.address


@pytest.fixture
def address_from_natural_person_participant_2(client: TestClient, specific_natural_person_participant_2):
    account_creation = Account.parse_obj({"address": "0xc0ffee254729296a45a3885639AC7E10F9d54979", "participant_id": specific_natural_person_participant_2.id, "balance": "0"})
    create_verified_account(account_creation, client, specific_natural_person_participant_2)
    return account_creation.address


@pytest.fixture
def addresses_example(client: TestClient, address_from_natural_person_participant, address_2_from_natural_person_participant, address_from_natural_person_participant_2):
    return [address_from_natural_person_participant, address_2_from_natural_person_participant, address_from_natural_person_participant_2, ]


@pytest.fixture
def addresses_to_update(client: TestClient, address_from_natural_person_participant, address_2_from_natural_person_participant, address_from_natural_person_participant_2):
    return [
        AddressWithBalance(address=address_from_natural_person_participant, balance=1000000000),
        AddressWithBalance(address=address_from_natural_person_participant_2, balance=2000000000),
        AddressWithBalance(address=address_2_from_natural_person_participant, balance=3000000000),
    ]

def create_verified_account(account_creation, client, specific_natural_person_participant):
    client.post("/accounts", data=account_creation.json())
    client.post(f"/controllers/{specific_natural_person_participant.id}/verifications/{account_creation.address}")