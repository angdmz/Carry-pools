import http

from fastapi.testclient import TestClient

from common import ObjRef
from logic.accounts import Account
from logic.accounts.business import RetrievedAccount
from logic.participants import RetrievedNaturalPerson


def test_create_account_flow(client: TestClient, specific_natural_person_participant: RetrievedNaturalPerson):
    account_creation = Account.parse_obj({"address": "0x42D429eaB483e88aBa5A80aF056dEC3610886101", "participant_id": specific_natural_person_participant.id})
    res = client.post("/accounts", data=account_creation.json())
    assert res.status_code == http.HTTPStatus.CREATED

    get_res = client.get(f"/accounts/{account_creation.address}")

    assert get_res.status_code == http.HTTPStatus.OK
    account = RetrievedAccount.parse_raw(get_res.content)
    assert account.address == account_creation.address
    assert account.controllers_count_is(1)
    assert account.has_controller_identified_as(specific_natural_person_participant.id)
