"""Firewall zones and policies."""

from __future__ import annotations

from ..api_handlers import ConfigurationHandler, SiteResourceHandler
from ..models.api import SiteResourceRequest
from ..models.firewall import FirewallPolicy, FirewallZone


class FirewallZones(SiteResourceHandler[FirewallZone]):
    """The firewall zones of the active site, keyed by UUID."""

    item_cls = FirewallZone
    collection = "firewall/zones"


class FirewallPolicies(ConfigurationHandler[FirewallPolicy]):
    """The firewall policies of the active site, keyed by UUID.

    The console orders policies itself; `index` is set through a separate
    ordering endpoint, so it is left out of updates.
    """

    item_cls = FirewallPolicy
    collection = "firewall/policies"
    read_only_keys = ("id", "metadata", "index")

    async def set_logging(self, policy_id: str, enabled: bool) -> FirewallPolicy:
        """Turn syslog logging of matches on or off.

        The one field the API can change without replacing the policy.
        """
        response = await self.api_client.request(
            SiteResourceRequest.create_patch(
                self.api_client.site_id,
                self.collection,
                policy_id,
                {"loggingEnabled": enabled},
            )
        )
        raw = response["data"][0]
        self.process_item(raw)
        return FirewallPolicy(raw)
