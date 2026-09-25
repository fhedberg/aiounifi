"""Test the WiFi broadcasts interface."""

import orjson
import pytest

from aiounifi.errors import RequestError
from aiounifi.interfaces.api_handlers import ItemEvent
from aiounifi.network.v1.api_client import ApiClient

from .conftest import SITE_ID, envelope, requests_to, url_pattern

BROADCAST_ID = "3b7f1c52-8e0a-4d1f-9a55-0c2d7e9b4a11"
PATH = f"/v1/sites/{SITE_ID}/wifi/broadcasts"

OVERVIEW = {
    "type": "STANDARD",
    "id": BROADCAST_ID,
    "name": "Home",
    "metadata": {"origin": "USER_DEFINED"},
    "enabled": True,
    "network": {
        "type": "SPECIFIC",
        "networkId": "9d2e3f40-0000-4000-8000-000000000010",
    },
    "securityConfiguration": {"type": "WPA2_PERSONAL"},
}
DETAILS = {
    **OVERVIEW,
    "securityConfiguration": {
        "type": "WPA2_PERSONAL",
        "passphrase": "correct horse",
        "fastRoamingEnabled": False,
    },
    "hideName": False,
    "clientIsolationEnabled": False,
    "multicastToUnicastConversionEnabled": False,
    "uapsdEnabled": True,
    "channel2gLockedTo6": False,
    "dtimPeriod2gLockedTo3": False,
}
OPEN_DETAILS = {
    **DETAILS,
    "id": "5c6d7e8f-0000-4000-8000-000000000020",
    "name": "Guest",
    "network": {"type": "NATIVE"},
    "securityConfiguration": {"type": "OPEN"},
    "hideName": True,
}


async def test_update_and_properties(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Broadcasts are cached by UUID; the overview has no passphrase."""
    mock_aioresponse.get(url_pattern(PATH), payload=envelope([OVERVIEW]))
    broadcasts = network_client_with_site.wifi_broadcasts

    await broadcasts.update()

    home = broadcasts[BROADCAST_ID]
    assert home.broadcast_id == BROADCAST_ID
    assert home.name == "Home"
    assert home.type == "STANDARD"
    assert home.enabled is True
    assert home.origin == "USER_DEFINED"
    assert home.security_type == "WPA2_PERSONAL"
    assert home.passphrase is None
    assert home.hide_name is None
    assert home.network_id == "9d2e3f40-0000-4000-8000-000000000010"


async def test_get_details_refreshes_cache(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Details carry the passphrase and replace the cached overview."""
    mock_aioresponse.get(url_pattern(f"{PATH}/{BROADCAST_ID}"), payload=DETAILS)
    broadcasts = network_client_with_site.wifi_broadcasts

    home = await broadcasts.get_details(BROADCAST_ID)

    assert home.passphrase == "correct horse"
    assert home.hide_name is False
    assert broadcasts[BROADCAST_ID].passphrase == "correct horse"


async def test_set_enabled_puts_the_whole_object(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Disabling reads the details, drops read-only fields and PUTs the rest."""
    mock_aioresponse.get(url_pattern(f"{PATH}/{BROADCAST_ID}"), payload=DETAILS)
    mock_aioresponse.put(
        url_pattern(f"{PATH}/{BROADCAST_ID}"), payload={**DETAILS, "enabled": False}
    )
    broadcasts = network_client_with_site.wifi_broadcasts
    events: list[tuple[ItemEvent, str]] = []
    broadcasts.subscribe(lambda event, obj_id: events.append((event, obj_id)))

    home = await broadcasts.set_enabled(BROADCAST_ID, False)

    assert home.enabled is False
    assert broadcasts[BROADCAST_ID].enabled is False
    assert events == [
        (ItemEvent.ADDED, BROADCAST_ID),
        (ItemEvent.CHANGED, BROADCAST_ID),
    ]
    (call,) = requests_to(mock_aioresponse, "put", f"{PATH}/{BROADCAST_ID}")
    sent = orjson.loads(call.kwargs["data"])
    assert sent["enabled"] is False
    assert "id" not in sent
    assert "metadata" not in sent
    assert sent["securityConfiguration"]["passphrase"] == "correct horse"


async def test_update_with_empty_response_keeps_changes(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """A console that answers an update with no body still updates the cache."""
    mock_aioresponse.get(url_pattern(f"{PATH}/{BROADCAST_ID}"), payload=DETAILS)
    mock_aioresponse.put(url_pattern(f"{PATH}/{BROADCAST_ID}"), body=b"")

    home = await network_client_with_site.wifi_broadcasts.set_enabled(
        BROADCAST_ID, False
    )

    assert home.enabled is False
    assert home.broadcast_id == BROADCAST_ID


async def test_set_passphrase(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """The passphrase is changed inside the security configuration."""
    new = {
        **DETAILS,
        "securityConfiguration": {
            **DETAILS["securityConfiguration"],
            "passphrase": "battery staple",
        },
    }
    mock_aioresponse.get(url_pattern(f"{PATH}/{BROADCAST_ID}"), payload=DETAILS)
    mock_aioresponse.get(url_pattern(f"{PATH}/{BROADCAST_ID}"), payload=DETAILS)
    mock_aioresponse.put(url_pattern(f"{PATH}/{BROADCAST_ID}"), payload=new)

    home = await network_client_with_site.wifi_broadcasts.set_passphrase(
        BROADCAST_ID, "battery staple"
    )

    assert home.passphrase == "battery staple"
    (call,) = requests_to(mock_aioresponse, "put", f"{PATH}/{BROADCAST_ID}")
    assert orjson.loads(call.kwargs["data"])["securityConfiguration"] == {
        "type": "WPA2_PERSONAL",
        "passphrase": "battery staple",
        "fastRoamingEnabled": False,
    }


async def test_set_passphrase_on_open_network_fails(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """An open network has no passphrase to change."""
    mock_aioresponse.get(
        url_pattern(f"{PATH}/{OPEN_DETAILS['id']}"), payload=OPEN_DETAILS
    )

    with pytest.raises(RequestError, match="OPEN"):
        await network_client_with_site.wifi_broadcasts.set_passphrase(
            OPEN_DETAILS["id"], "whatever1"
        )
    assert not requests_to(mock_aioresponse, "put", f"{PATH}/{OPEN_DETAILS['id']}")


@pytest.mark.parametrize("details", [DETAILS, OPEN_DETAILS])
async def test_generate_qr_code(
    mock_aioresponse, network_client_with_site: ApiClient, details
) -> None:
    """A PNG comes back for protected and open networks alike."""
    mock_aioresponse.get(url_pattern(f"{PATH}/{details['id']}"), payload=details)

    png = await network_client_with_site.wifi_broadcasts.generate_qr_code(
        details["id"], dark="#000000", light="#ffffff", border=2
    )

    assert png.startswith(b"\x89PNG")


async def test_list_page(mock_aioresponse, network_client_with_site: ApiClient) -> None:
    """One page, with a filter, leaves the cache alone."""
    mock_aioresponse.get(url_pattern(PATH), payload=envelope([OVERVIEW]))

    (home,) = await network_client_with_site.wifi_broadcasts.list_page(
        filter_value="enabled.eq(true)"
    )

    assert home.name == "Home"
    assert not network_client_with_site.wifi_broadcasts.items()
    (call,) = requests_to(mock_aioresponse, "get", PATH)
    assert call.kwargs["params"]["filter"] == "enabled.eq(true)"
