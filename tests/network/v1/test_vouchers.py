"""Test the hotspot vouchers interface."""

import orjson

from aiounifi.interfaces.api_handlers import ItemEvent
from aiounifi.network.v1.api_client import ApiClient

from .conftest import SITE_ID, envelope, requests_to, url_pattern

PATH = f"/v1/sites/{SITE_ID}/hotspot/vouchers"
UNUSED = {
    "id": "4d5e6f70-0000-4000-8000-000000000400",
    "createdAt": "2026-09-25T08:00:00Z",
    "name": "Weekend guests",
    "code": "4861409510",
    "authorizedGuestCount": 0,
    "timeLimitMinutes": 1440,
    "expired": False,
}
USED = {
    **UNUSED,
    "id": "4d5e6f70-0000-4000-8000-000000000401",
    "code": "9021736648",
    "authorizedGuestLimit": 2,
    "authorizedGuestCount": 1,
    "activatedAt": "2026-09-25T09:00:00Z",
    "expiresAt": "2026-09-26T09:00:00Z",
    "dataUsageLimitMBytes": 2048,
    "rxRateLimitKbps": 10000,
    "txRateLimitKbps": 2000,
}


async def test_update_and_properties(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Vouchers are cached by UUID with their limits."""
    mock_aioresponse.get(url_pattern(PATH), payload=envelope([UNUSED, USED]))
    vouchers = network_client_with_site.vouchers

    await vouchers.update()

    unused = vouchers[UNUSED["id"]]
    assert unused.voucher_id == UNUSED["id"]
    assert unused.code == "4861409510"
    assert unused.name == "Weekend guests"
    assert unused.created_at == "2026-09-25T08:00:00Z"
    assert unused.expired is False
    assert unused.time_limit_minutes == 1440
    assert unused.authorized_guest_count == 0
    assert unused.authorized_guest_limit is None
    assert unused.activated_at is None
    assert unused.expires_at is None
    assert unused.data_usage_limit_mbytes is None
    assert unused.rx_rate_limit_kbps is None
    assert unused.tx_rate_limit_kbps is None

    used = vouchers[USED["id"]]
    assert used.authorized_guest_limit == 2
    assert used.authorized_guest_count == 1
    assert used.activated_at == "2026-09-25T09:00:00Z"
    assert used.expires_at == "2026-09-26T09:00:00Z"
    assert used.data_usage_limit_mbytes == 2048
    assert used.rx_rate_limit_kbps == 10000
    assert used.tx_rate_limit_kbps == 2000


async def test_generate(mock_aioresponse, network_client_with_site: ApiClient) -> None:
    """Generated vouchers are returned and cached."""
    mock_aioresponse.post(
        url_pattern(PATH), status=201, payload={"vouchers": [UNUSED, USED]}
    )
    vouchers = network_client_with_site.vouchers

    generated = await vouchers.generate(
        "Weekend guests",
        1440,
        count=2,
        authorized_guest_limit=2,
        data_usage_limit_mbytes=2048,
        rx_rate_limit_kbps=10000,
        tx_rate_limit_kbps=2000,
    )

    assert [voucher.code for voucher in generated] == ["4861409510", "9021736648"]
    assert set(vouchers) == {UNUSED["id"], USED["id"]}
    (call,) = requests_to(mock_aioresponse, "post", PATH)
    assert orjson.loads(call.kwargs["data"]) == {
        "name": "Weekend guests",
        "timeLimitMinutes": 1440,
        "count": 2,
        "authorizedGuestLimit": 2,
        "dataUsageLimitMBytes": 2048,
        "rxRateLimitKbps": 10000,
        "txRateLimitKbps": 2000,
    }


async def test_generate_minimal(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Limits left out are not sent."""
    mock_aioresponse.post(url_pattern(PATH), status=201, payload={"vouchers": [UNUSED]})

    await network_client_with_site.vouchers.generate("Weekend guests", 1440)

    (call,) = requests_to(mock_aioresponse, "post", PATH)
    assert orjson.loads(call.kwargs["data"]) == {
        "name": "Weekend guests",
        "timeLimitMinutes": 1440,
        "count": 1,
    }


async def test_delete(mock_aioresponse, network_client_with_site: ApiClient) -> None:
    """Deleting one voucher drops it from the cache and tells subscribers."""
    mock_aioresponse.get(url_pattern(PATH), payload=envelope([UNUSED]))
    mock_aioresponse.delete(
        url_pattern(f"{PATH}/{UNUSED['id']}"), payload={"vouchersDeleted": 1}
    )
    mock_aioresponse.delete(
        url_pattern(f"{PATH}/{USED['id']}"), payload={"vouchersDeleted": 1}
    )
    vouchers = network_client_with_site.vouchers
    await vouchers.update()
    events: list[tuple[ItemEvent, str]] = []
    vouchers.subscribe(lambda event, obj_id: events.append((event, obj_id)))

    await vouchers.delete(UNUSED["id"])
    await vouchers.delete(USED["id"])

    assert not vouchers.items()
    assert events == [(ItemEvent.DELETED, UNUSED["id"])]


async def test_delete_matching(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Deleting by filter reports the count and reloads the cache."""
    mock_aioresponse.get(url_pattern(PATH), payload=envelope([UNUSED, USED]))
    mock_aioresponse.delete(url_pattern(PATH), payload={"vouchersDeleted": 1})
    mock_aioresponse.get(url_pattern(PATH), payload=envelope([UNUSED]))
    vouchers = network_client_with_site.vouchers
    await vouchers.update()

    deleted = await vouchers.delete_matching("expired.eq(true)")

    assert deleted == 1
    assert set(vouchers) == {UNUSED["id"]}
    (call,) = requests_to(mock_aioresponse, "delete", PATH)
    assert call.kwargs["params"] == {"filter": "expired.eq(true)"}
