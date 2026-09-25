"""Test the ACL rules and DNS policies interfaces."""

import orjson

from aiounifi.network.v1.api_client import ApiClient

from .conftest import SITE_ID, envelope, requests_to, url_pattern

RULE_ID = "1f2e3d4c-0000-4000-8000-000000000200"
DNS_ID = "2a3b4c5d-0000-4000-8000-000000000300"
ACL = f"/v1/sites/{SITE_ID}/acl-rules"
DNS = f"/v1/sites/{SITE_ID}/dns/policies"

RULE = {
    "type": "IPV4",
    "id": RULE_ID,
    "enabled": True,
    "name": "Cameras stay local",
    "action": "BLOCK",
    "index": 0,
    "metadata": {"origin": "USER_DEFINED"},
    "sourceFilter": {"type": "NETWORKS", "networkIds": ["n1"]},
}
RECORD = {
    "type": "A_RECORD",
    "id": DNS_ID,
    "enabled": True,
    "domain": "ha.home.arpa",
    "ipv4Address": "10.0.0.20",
    "ttlSeconds": 300,
    "metadata": {"origin": "USER_DEFINED"},
}


async def test_acl_rules(mock_aioresponse, network_client_with_site: ApiClient) -> None:
    """ACL rules are cached by UUID and can be switched off."""
    mock_aioresponse.get(url_pattern(ACL), payload=envelope([RULE]))
    mock_aioresponse.get(url_pattern(f"{ACL}/{RULE_ID}"), payload=RULE)
    mock_aioresponse.put(
        url_pattern(f"{ACL}/{RULE_ID}"), payload={**RULE, "enabled": False}
    )
    rules = network_client_with_site.acl_rules

    await rules.update()
    rule = rules[RULE_ID]
    assert rule.rule_id == RULE_ID
    assert rule.name == "Cameras stay local"
    assert rule.type == "IPV4"
    assert rule.enabled is True
    assert rule.action == "BLOCK"
    assert rule.index == 0
    assert rule.origin == "USER_DEFINED"

    await rules.set_enabled(RULE_ID, False)

    assert rules[RULE_ID].enabled is False
    (call,) = requests_to(mock_aioresponse, "put", f"{ACL}/{RULE_ID}")
    assert {"id", "index", "metadata"}.isdisjoint(orjson.loads(call.kwargs["data"]))


async def test_dns_policies(
    mock_aioresponse, network_client_with_site: ApiClient
) -> None:
    """DNS policies are cached by UUID and can be switched off."""
    mock_aioresponse.get(url_pattern(DNS), payload=envelope([RECORD]))
    mock_aioresponse.get(url_pattern(f"{DNS}/{DNS_ID}"), payload=RECORD)
    mock_aioresponse.put(
        url_pattern(f"{DNS}/{DNS_ID}"), payload={**RECORD, "enabled": False}
    )
    policies = network_client_with_site.dns_policies

    await policies.update()
    record = policies[DNS_ID]
    assert record.policy_id == DNS_ID
    assert record.type == "A_RECORD"
    assert record.domain == "ha.home.arpa"
    assert record.enabled is True
    assert record.origin == "USER_DEFINED"

    await policies.set_enabled(DNS_ID, False)

    assert policies[DNS_ID].enabled is False
    (call,) = requests_to(mock_aioresponse, "put", f"{DNS}/{DNS_ID}")
    sent = orjson.loads(call.kwargs["data"])
    assert sent["ipv4Address"] == "10.0.0.20"
    assert sent["enabled"] is False
