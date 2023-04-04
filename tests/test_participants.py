import http

from starlette.testclient import TestClient

from participants.business import RetrievedParticipant, Participant
from tests.schemas import ObjRef


def test_participants_flow(client: TestClient):
    participant_creation_data = Participant(name="A participant")
    res = client.post("/participants", data=participant_creation_data.json())
    assert res.status_code == http.HTTPStatus.CREATED

    participant_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/participants/{participant_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    participant = RetrievedParticipant.parse_raw(get_res.content)
    assert participant.is_named("A participant")
