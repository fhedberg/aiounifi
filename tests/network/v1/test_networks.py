"""Test the networks interface."""

import orjson

from aiounifi.network.v1.api_client import ApiClient

from .conftest import SITE_ID, envelope, requests_to, url_pattern

NETWORK_ID = "9d2e3f40-0000-4000-8000-000000000010"
PATH = f"/v1/sites/{SITE_ID}/networks"

IOT = {
    "management": "GATEWAY",
    "id": NETWORK_ID,
    "name": "IoT",
    "enabled": True,
    "vlanId": 30,
    "metadata": {"origin": "USER_DEFINED"},
    "default": False,
}
IOT_DETAILS = {**IOT, "isolationEnabled": True, "internetAccessEnabled": True}


async def test_update_and_properties(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Networks are cached by UUID."""
    mock_aioresponse.get(url_pattern(PATH), payload=envelope([IOT]))
    networks = network_client_with_site.networks

    await networks.update()

    iot = networks[NETWORK_ID]
    assert iot.network_id == NETWORK_ID
    assert iot.name == "IoT"
    assert iot.enabled is True
    assert iot.default is False
    assert iot.management == "GATEWAY"
    assert iot.vlan_id == 30
    assert iot.origin == "USER_DEFINED"


async def test_set_enabled_leaves_out_default(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """`default` is read-only and is not sent back."""
    mock_aioresponse.get(url_pattern(f"{PATH}/{NETWORK_ID}"), payload=IOT_DETAILS)
    mock_aioresponse.put(
        url_pattern(f"{PATH}/{NETWORK_ID}"), payload={**IOT_DETAILS, "enabled": False}
    )

    iot = await network_client_with_site.networks.set_enabled(NETWORK_ID, False)

    assert iot.enabled is False
    (call,) = requests_to(mock_aioresponse, "put", f"{PATH}/{NETWORK_ID}")
    sent = orjson.loads(call.kwargs["data"])
    assert sent == {
        "management": "GATEWAY",
        "name": "IoT",
        "enabled": False,
        "vlanId": 30,
        "isolationEnabled": True,
        "internetAccessEnabled": True,
    }
