import http

from starlette.testclient import TestClient

from common import ObjRef
from enums import SortOrder
from logic.customers import Customer
from logic.participants import ParticipantListing


def test_retrieve_non_existent_customer(client: TestClient):
    get_res = client.get("/customers/9515d9bb-d4d6-4952-9003-9d7e0436fe58")
    assert get_res.status_code == http.HTTPStatus.NOT_FOUND
    content = get_res.json()
    assert content["detail"] == 'Customer not found. ID: 9515d9bb-d4d6-4952-9003-9d7e0436fe58'


def test_customer_flow(client: TestClient):
    customer = Customer.parse_obj(dict(name="My Customer"))
    res = client.post("/customers", data=customer.json())
    assert res.status_code == http.HTTPStatus.CREATED

    customer_id = ObjRef.parse_raw(res.content).id

    get_res = client.get(f"/customers/{customer_id}")

    assert get_res.status_code == http.HTTPStatus.OK
    customer = Customer.parse_raw(get_res.content)
    assert customer.is_named("My Customer")

    update_data = Customer.parse_obj({"name":"My updated name"})
    update_res = client.patch(f"/customers/{customer_id}", data=update_data.json())
    assert update_res.status_code == http.HTTPStatus.NO_CONTENT

    get_res = client.get(f"/customers/{customer_id}")
    customer = Customer.parse_raw(get_res.content)
    assert customer.is_named("My updated name")


def test_all_listing(client: TestClient, customers_example):
    params = {
        "limit": 10,
        "sort": SortOrder.ASC.value,
    }
    res = client.get(f"/customers", params=params)
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
    res = client.get(f"/customers", params=params)
    assert res.status_code == http.HTTPStatus.OK
    listing = ParticipantListing.parse_raw(res.content)
    assert listing.next_url is None

    assert len(listing.results) == 0
