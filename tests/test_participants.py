import http

from starlette.testclient import TestClient

from common import ObjRef
from enums import SortOrder
from logic.participants import CompanyParticipant, RetrievedCompanyParticipant, UpdateCompanyParticipant
from logic.participants import GovernmentOrganismParticipant, RetrievedGovernmentOrganismParticipant, \
    UpdateGovernmentOrganismParticipant
from logic.participants import ParticipantListing
from logic.participants import RetrievedAcademicParticipant, UpdateAcademicParticipant, \
    RetrievedSchoolParticipant, UniversityParticipant
from logic.participants.natural_person import NaturalPersonParticipant, RetrievedNaturalPerson, \
    UpdateNaturalPersonParticipant


def test_retrieve_non_existent_participant(client: TestClient):
    get_res = client.get("/participants/9515d9bb-d4d6-4952-9003-9d7e0436fe58")
    assert get_res.status_code == http.HTTPStatus.NOT_FOUND
    content = get_res.json()
    assert content["detail"] == 'Participant not found. ID: 9515d9bb-d4d6-4952-9003-9d7e0436fe58'


def test_natural_person_participant_flow(client: TestClient):
    participant_creation_data = NaturalPersonParticipant.parse_obj(dict(first_name="John Sunday", last_name="Peron", type="NATURAL_PERSON", identification=dict(type="DNI", value="37993169")))
    res = client.post("/participants", data=participant_creation_data.json())
    assert res.status_code == http.HTTPStatus.CREATED

    participant_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/participants/{participant_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    participant = RetrievedNaturalPerson.parse_raw(get_res.content)
    assert participant.is_named("John Sunday", "Peron")
    assert participant.has_dni("37993169")

    update_data = UpdateNaturalPersonParticipant.parse_obj({"first_name":"Juan Domingo", "identification":{"value": 37993168}})
    update_res = client.patch(f"/participants/{participant_id}", data=update_data.json())
    assert update_res.status_code == http.HTTPStatus.NO_CONTENT

    get_res = client.get(f"/participants/{participant_id}")
    participant = RetrievedNaturalPerson.parse_raw(get_res.content)
    assert participant.is_named("Juan Domingo", "Peron")
    assert participant.has_dni("37993168")
    assert not participant.is_verified

def test_company_participant_flow(client: TestClient):
    participant_creation_data = CompanyParticipant(full_name="A company", cuit="20379931694", type="COMPANY")
    res = client.post("/participants", data=participant_creation_data.json())
    assert res.status_code == http.HTTPStatus.CREATED

    participant_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/participants/{participant_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    participant = RetrievedCompanyParticipant.parse_raw(get_res.content)
    assert participant.is_named("A company")
    assert participant.has_cuit("20379931694")
    assert not participant.is_verified
    update_data = UpdateCompanyParticipant.parse_obj({"cuit":"20379931593"})
    update_res = client.patch(f"/participants/{participant_id}", data=update_data.json())
    assert update_res.status_code == http.HTTPStatus.NO_CONTENT

    get_res = client.get(f"/participants/{participant_id}")
    participant = RetrievedCompanyParticipant.parse_raw(get_res.content)
    assert participant.is_named("A company")
    assert participant.has_cuit("20379931593")
    assert not participant.is_verified


def test_government_organism_participant_flow(client: TestClient):
    participant_creation_data = GovernmentOrganismParticipant(full_name="Some direction", sector="National", type="GOVERNMENT_ORGANISM")
    res = client.post("/participants", data=participant_creation_data.json())
    assert res.status_code == http.HTTPStatus.CREATED

    participant_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/participants/{participant_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    participant = RetrievedGovernmentOrganismParticipant.parse_raw(get_res.content)
    assert participant.is_named("Some direction")

    update_data = UpdateGovernmentOrganismParticipant.parse_obj({"sector":"Municipal"})
    update_res = client.patch(f"/participants/{participant_id}", data=update_data.json())
    assert update_res.status_code == http.HTTPStatus.NO_CONTENT

    get_res = client.get(f"/participants/{participant_id}")
    participant = RetrievedGovernmentOrganismParticipant.parse_raw(get_res.content)
    assert participant.is_named("Some direction")
    assert participant.is_sector("Municipal")
    assert not participant.is_verified

def test_university_participant_flow(client: TestClient):
    participant_creation_data = UniversityParticipant(full_name="UBA")
    res = client.post("/participants", data=participant_creation_data.json())
    assert res.status_code == http.HTTPStatus.CREATED

    participant_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/participants/{participant_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    participant = RetrievedAcademicParticipant.parse_raw(get_res.content)
    assert participant.is_named("UBA")

    update_data = UpdateAcademicParticipant.parse_obj({"education_level":"SCHOOL"})
    update_res = client.patch(f"/participants/{participant_id}", data=update_data.json())
    assert update_res.status_code == http.HTTPStatus.NO_CONTENT

    get_res = client.get(f"/participants/{participant_id}")
    participant = RetrievedSchoolParticipant.parse_raw(get_res.content)
    assert participant.is_named("UBA")
    assert not participant.is_verified

def test_all_listing(client: TestClient, customers_example):
    params = {
        "limit": 10,
        "sort": SortOrder.ASC.value,
    }
    res = client.get(f"/participants", params=params)
    assert res.status_code == http.HTTPStatus.OK
    listing = ParticipantListing.parse_raw(res.content)
    assert listing.next_url is None

    assert len(listing.results) == 4
    for i in range(4):
        assert customers_example[i] in listing.results


def test_all_listing_empty(client: TestClient):
    params = {
        "limit": 10,
        "sort": SortOrder.ASC.value,
    }
    res = client.get(f"/participants", params=params)
    assert res.status_code == http.HTTPStatus.OK
    listing = ParticipantListing.parse_raw(res.content)
    assert listing.next_url is None

    assert len(listing.results) == 0
