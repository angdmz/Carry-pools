import http

from fastapi.testclient import TestClient

from logic.accounts import Account
from logic.accounts.business import RetrievedAccount, AddressCollection, AddressListing
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


def test_verify_non_existing_account_nor_participant(client: TestClient, specific_natural_person_participant):
    res_verification = client.post(f"/controllers/{specific_natural_person_participant.id}/verifications/0xc0ffee254729296a45a3885639AC7E10F9d54979")
    assert res_verification.status_code == http.HTTPStatus.NOT_FOUND
    content = res_verification.json()
    assert content["detail"] == f'No controller found: address 0xc0ffee254729296a45a3885639AC7E10F9d54979 - participant ID: {specific_natural_person_participant.id}'

    res_verification = client.post("/controllers/53b39a76-0e25-4d13-a64f-7b87b00295d8/verifications/0xc0ffee254729296a45a3885639AC7E10F9d54979")
    assert res_verification.status_code == http.HTTPStatus.NOT_FOUND
    content = res_verification.json()
    assert content["detail"] == 'No controller found: address 0xc0ffee254729296a45a3885639AC7E10F9d54979 - participant ID: 53b39a76-0e25-4d13-a64f-7b87b00295d8'


def test_list_addresses_flow_empty(client: TestClient):
    res = client.get("/accounts")
    assert res.status_code == http.HTTPStatus.OK
    listing = AddressListing.parse_raw(res.content)
    assert len(listing.results) == 0
    assert listing.next_url is None


def test_address_listing(client: TestClient, addresses_example, specific_natural_person_participant):
    res = client.get("/accounts")
    assert res.status_code == http.HTTPStatus.OK
    listing = AddressListing.parse_raw(res.content)

    assert len(listing.results) == len(addresses_example)
    result_addresses = [result.address for result in listing.results]
    for i in addresses_example:
        assert i in result_addresses

    res_participant_ids_filter = client.get("/accounts", params={"participant_ids": [specific_natural_person_participant.id]})
    assert res_participant_ids_filter.status_code == http.HTTPStatus.OK

    listing = AddressListing.parse_raw(res.content)

    assert len(listing.results) == len(addresses_example)
    result_addresses = [result.address for result in listing.results]
    for i in addresses_example:
        assert i in result_addresses

def test_address_bulk_update_balance(client: TestClient, addresses_to_update):
    params = AddressCollection(addresses=addresses_to_update)
    res_bulk_update = client.patch("/accounts/balances", data=params.json())
    assert res_bulk_update.status_code == http.HTTPStatus.OK

    for address in addresses_to_update:
        res_retrieved = client.get(f"/accounts/{address.address}")
        retrieved_account = RetrievedAccount.parse_raw(res_retrieved.content)
        assert retrieved_account.has_balance(address.balance)
