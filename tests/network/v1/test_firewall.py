"""Test the firewall zones and policies interfaces."""

import orjson

from aiounifi.network.v1.api_client import ApiClient

from .conftest import SITE_ID, envelope, requests_to, url_pattern

ZONE_INTERNAL = "0a1b2c3d-0000-4000-8000-000000000001"
ZONE_EXTERNAL = "0a1b2c3d-0000-4000-8000-000000000002"
POLICY_ID = "7e8f9a0b-0000-4000-8000-000000000100"
ZONES = f"/v1/sites/{SITE_ID}/firewall/zones"
POLICIES = f"/v1/sites/{SITE_ID}/firewall/policies"

INTERNAL = {
    "id": ZONE_INTERNAL,
    "name": "Internal",
    "networkIds": ["9d2e3f40-0000-4000-8000-000000000010"],
    "metadata": {"origin": "SYSTEM_DEFINED"},
}
BLOCK_KIDS = {
    "id": POLICY_ID,
    "enabled": True,
    "name": "Block kids at night",
    "description": "School nights",
    "action": {"type": "BLOCK"},
    "source": {"zoneId": ZONE_INTERNAL},
    "destination": {"zoneId": ZONE_EXTERNAL},
    "ipProtocolScope": {"ipVersion": "IPV4_AND_IPV6"},
    "loggingEnabled": False,
    "index": 10000,
    "metadata": {"origin": "USER_DEFINED"},
}
SYSTEM_POLICY = {
    **BLOCK_KIDS,
    "id": "7e8f9a0b-0000-4000-8000-000000000101",
    "name": "Allow Return Traffic",
    "action": {"type": "ALLOW"},
    "metadata": {"origin": "SYSTEM_DEFINED"},
}
del SYSTEM_POLICY["description"]


async def test_zones(mock_aioresponse, network_client_with_site: ApiClient) -> None:
    """Zones are cached by UUID."""
    mock_aioresponse.get(url_pattern(ZONES), payload=envelope([INTERNAL]))
    zones = network_client_with_site.firewall_zones

    await zones.update()

    internal = zones[ZONE_INTERNAL]
    assert internal.zone_id == ZONE_INTERNAL
    assert internal.name == "Internal"
    assert internal.network_ids == ["9d2e3f40-0000-4000-8000-000000000010"]
    assert internal.origin == "SYSTEM_DEFINED"


async def test_policies(mock_aioresponse, network_client_with_site: ApiClient) -> None:
    """Policies are cached by UUID and say whether the console made them."""
    mock_aioresponse.get(
        url_pattern(POLICIES), payload=envelope([BLOCK_KIDS, SYSTEM_POLICY])
    )
    policies = network_client_with_site.firewall_policies

    await policies.update()

    block = policies[POLICY_ID]
    assert block.policy_id == POLICY_ID
    assert block.name == "Block kids at night"
    assert block.description == "School nights"
    assert block.enabled is True
    assert block.index == 10000
    assert block.action == "BLOCK"
    assert block.source_zone_id == ZONE_INTERNAL
    assert block.destination_zone_id == ZONE_EXTERNAL
    assert block.logging_enabled is False
    assert block.origin == "USER_DEFINED"
    assert block.predefined is False

    system = policies[SYSTEM_POLICY["id"]]
    assert system.description is None
    assert system.predefined is True


async def test_set_enabled_leaves_out_index(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """`index` is set through the ordering endpoint, not on update."""
    mock_aioresponse.get(url_pattern(f"{POLICIES}/{POLICY_ID}"), payload=BLOCK_KIDS)
    mock_aioresponse.put(
        url_pattern(f"{POLICIES}/{POLICY_ID}"), payload={**BLOCK_KIDS, "enabled": False}
    )

    policy = await network_client_with_site.firewall_policies.set_enabled(
        POLICY_ID, False
    )

    assert policy.enabled is False
    (call,) = requests_to(mock_aioresponse, "put", f"{POLICIES}/{POLICY_ID}")
    sent = orjson.loads(call.kwargs["data"])
    assert sent["enabled"] is False
    assert {"id", "index", "metadata"}.isdisjoint(sent)


async def test_set_logging_patches(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """Logging is the one field changed with PATCH."""
    mock_aioresponse.patch(
        url_pattern(f"{POLICIES}/{POLICY_ID}"),
        payload={**BLOCK_KIDS, "loggingEnabled": True},
    )
    policies = network_client_with_site.firewall_policies

    policy = await policies.set_logging(POLICY_ID, True)

    assert policy.logging_enabled is True
    assert policies[POLICY_ID].logging_enabled is True
    (call,) = requests_to(mock_aioresponse, "patch", f"{POLICIES}/{POLICY_ID}")
    assert call.kwargs["data"] == b'{"loggingEnabled":true}'
