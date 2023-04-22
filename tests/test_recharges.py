import http

from fastapi.testclient import TestClient

from common import ObjRef
from enums import SortOrder, RechargeStatus
from logic.accounts.business import RetrievedAccount
from logic.recharges.recharge import RetrievedWaitingRecharge, RetrievedSatisfiedRecharge, RetrievedRejectedRecharge, \
    RechargeListing


def test_satisfied_recharge_flow(client: TestClient, address_from_natural_person_participant):

    res_recharges = client.post(f"/accounts/{address_from_natural_person_participant}/recharges")
    assert res_recharges.status_code == http.HTTPStatus.ACCEPTED

    recharge_id = ObjRef.parse_raw(res_recharges.content).id

    get_recharge_res = client.get(f"/recharges/{recharge_id}")
    assert get_recharge_res.status_code == http.HTTPStatus.OK

    retrieved_recharge = RetrievedWaitingRecharge.parse_raw(get_recharge_res.content)
    assert retrieved_recharge.is_for_address(address_from_natural_person_participant)

    get_res = client.get(f"/accounts/{address_from_natural_person_participant}")
    retrieved_account = RetrievedAccount.parse_raw(get_res.content)

    assert retrieved_account.has_balance(0)

    res_satisfy_recharge = client.post(f"/recharges/{recharge_id}/satisfy")
    assert res_satisfy_recharge.status_code == http.HTTPStatus.ACCEPTED

    get_recharge_res = client.get(f"/recharges/{recharge_id}")
    assert get_recharge_res.status_code == http.HTTPStatus.OK

    retrieved_recharge = RetrievedSatisfiedRecharge.parse_raw(get_recharge_res.content)
    assert retrieved_recharge.is_for_address(address_from_natural_person_participant)


def test_rejected_recharge_flow(client: TestClient, address_from_natural_person_participant):

    res_recharges = client.post(f"/accounts/{address_from_natural_person_participant}/recharges")
    assert res_recharges.status_code == http.HTTPStatus.ACCEPTED

    recharge_id = ObjRef.parse_raw(res_recharges.content).id

    get_recharge_res = client.get(f"/recharges/{recharge_id}")
    assert get_recharge_res.status_code == http.HTTPStatus.OK

    retrieved_recharge = RetrievedWaitingRecharge.parse_raw(get_recharge_res.content)
    assert retrieved_recharge.is_for_address(address_from_natural_person_participant)

    get_res = client.get(f"/accounts/{address_from_natural_person_participant}")
    retrieved_account = RetrievedAccount.parse_raw(get_res.content)

    assert retrieved_account.has_balance(0)

    res_satisfy_recharge = client.post(f"/recharges/{recharge_id}/reject")
    assert res_satisfy_recharge.status_code == http.HTTPStatus.ACCEPTED

    get_recharge_res = client.get(f"/recharges/{recharge_id}")
    assert get_recharge_res.status_code == http.HTTPStatus.OK

    retrieved_recharge = RetrievedRejectedRecharge.parse_raw(get_recharge_res.content)
    assert retrieved_recharge.is_for_address(address_from_natural_person_participant)


def test_list_recharges_flow(client: TestClient, recharges_example):
    res = client.get("/recharges")
    recharges_example.sort(key=lambda x: x.created_at, reverse=True)
    assert res.status_code == http.HTTPStatus.OK
    listing = RechargeListing.parse_raw(res.content)

    assert len(listing.results) == 10
    for recharge in listing.results:
        assert recharge in recharges_example

    res_second = client.get(f"/recharges?{listing.next_url}")
    assert res_second.status_code == http.HTTPStatus.OK

    second_listing = RechargeListing.parse_raw(res_second.content)
    assert len(second_listing.results) == 2
    for recharge in second_listing.results:
        assert recharge in recharges_example

    combined = {recharge.id for recharge in listing.results + second_listing.results}
    assert combined == {recharge.id for recharge in recharges_example}


    params = {
        "status": RechargeStatus.SATISFIED.value
    }
    third_res = client.get("/recharges", params=params)
    assert third_res.status_code == http.HTTPStatus.OK

    third_listing = RechargeListing.parse_raw(third_res.content)
    only_satisfied_recharges = {recharge.id for recharge in recharges_example if recharge.status == RechargeStatus.SATISFIED}
    assert {recharge.id for recharge in third_listing.results} == only_satisfied_recharges