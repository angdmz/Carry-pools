import http

from fastapi.testclient import TestClient

from logic.accounts import Account
from logic.accounts.business import RetrievedAccount, AddressCollection
from logic.participants import RetrievedNaturalPerson


def test_account_flow(client: TestClient,
                      specific_natural_person_participant: RetrievedNaturalPerson,
                      balance_limit_per_account):
    account_creation = Account.parse_obj({"address": "0x42D429eaB483e88aBa5A80aF056dEC3610886101", "participant_id": specific_natural_person_participant.id, "balance": "0"})
    res = client.post("/accounts", data=account_creation.json())
    assert res.status_code == http.HTTPStatus.CREATED

    get_res = client.get(f"/accounts/{account_creation.address}")

    assert get_res.status_code == http.HTTPStatus.OK
    account = RetrievedAccount.parse_raw(get_res.content)
    assert account.address == account_creation.address
    assert account.controllers_count_is(1)
    assert account.has_controller_identified_as(specific_natural_person_participant.id)
    assert account.has_balance(account_creation.balance)
    assert not account.controller_identified_as_is_verified(specific_natural_person_participant.id)
    assert account.balance_limit_is(balance_limit_per_account)


    res_verification = client.post(f"/controllers/{specific_natural_person_participant.id}/verifications/{account_creation.address}")
    assert res_verification.status_code == http.HTTPStatus.ACCEPTED

    get_res = client.get(f"/accounts/{account_creation.address}")

    assert get_res.status_code == http.HTTPStatus.OK
    account = RetrievedAccount.parse_raw(get_res.content)
    assert account.address == account_creation.address
    assert account.controllers_count_is(1)
    assert account.has_controller_identified_as(specific_natural_person_participant.id)
    assert account.controller_identified_as_is_verified(specific_natural_person_participant.id)
    assert account.has_balance(account_creation.balance)


def test_address_bulk_update_balance(client: TestClient, addresses):
    params = AddressCollection(addresses=addresses)
    res_bulk_update = client.patch("/accounts/balances", data=params.json())
    assert res_bulk_update.status_code == http.HTTPStatus.OK

    for address in addresses:
        res_retrieved = client.get(f"/accounts/{address.address}")
        retrieved_account = RetrievedAccount.parse_raw(res_retrieved.content)
        assert retrieved_account.has_balance(address.balance)
