import http
from typing import List

from starlette.testclient import TestClient

from enums import AcademicType, SortOrder
from participants.business import CompanyParticipant, \
    RetrievedCompanyParticipant, GovernmentOrganismParticipant, RetrievedGovernmentOrganismParticipant, \
    AcademicParticipant, RetrievedAcademicParticipant, Participant, ParticipantListing
from participants.natural_person import NaturalPersonParticipant, RetrievedNaturalPerson, UpdateNaturalPersonParticipant
from tests.schemas import ObjRef


def test_natural_person_participant_flow(client: TestClient):
    participant_creation_data = NaturalPersonParticipant.parse_obj(dict(first_name="John Sunday", last_name="Peron", type="NATURAL_PERSON", identification=dict(type="DNI", id="37993169")))
    res = client.post("/participants", data=participant_creation_data.json())
    assert res.status_code == http.HTTPStatus.CREATED

    participant_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/participants/{participant_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    participant = RetrievedNaturalPerson.parse_raw(get_res.content)
    assert participant.is_named("John Sunday", "Peron")
    assert participant.has_dni("37993169")

    update_data = UpdateNaturalPersonParticipant.parse_obj({"first_name":"Juan Domingo", "identification":{"id": 37993168}})
    update_res = client.patch(f"/participants/{participant_id}", data=update_data.json())
    assert update_res.status_code == http.HTTPStatus.NO_CONTENT

    get_res = client.get(f"/participants/{participant_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    participant = RetrievedNaturalPerson.parse_raw(get_res.content)
    assert participant.is_named("Juan Domingo", "Peron")
    assert participant.has_dni("37993168")
    assert not participant.is_verified

def test_company_participant_flow(client: TestClient):
    participant_creation_data = CompanyParticipant(full_name="A company", cuit="20379931694")
    res = client.post("/participants", data=participant_creation_data.json())
    assert res.status_code == http.HTTPStatus.CREATED

    participant_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/participants/{participant_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    participant = RetrievedCompanyParticipant.parse_raw(get_res.content)
    assert participant.is_named("A company")

def test_government_organism_participant_flow(client: TestClient):
    participant_creation_data = GovernmentOrganismParticipant(full_name="A participant", sector="National")
    res = client.post("/participants", data=participant_creation_data.json())
    assert res.status_code == http.HTTPStatus.CREATED

    participant_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/participants/{participant_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    participant = RetrievedGovernmentOrganismParticipant.parse_raw(get_res.content)
    assert participant.is_named("A participant")

def test_university_participant_flow(client: TestClient):
    participant_creation_data = AcademicParticipant(full_name="A participant", education_level=AcademicType.UNIVERSITY)
    res = client.post("/participants", data=participant_creation_data.json())
    assert res.status_code == http.HTTPStatus.CREATED

    participant_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/participants/{participant_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    participant = RetrievedAcademicParticipant.parse_raw(get_res.content)
    assert participant.is_named("A participant")

def test_all_listing(client: TestClient, example: List[Participant]):
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
        assert example[i] in listing.results
