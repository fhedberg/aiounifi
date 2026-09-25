"""Firewall zones and policies."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict

from ....models.api import ApiItem
from .api import EntityMetadata


class FirewallZoneData(TypedDict):
    """One firewall zone."""

    id: str
    name: str
    networkIds: list[str]
    metadata: EntityMetadata


class FirewallZone(ApiItem):
    """A firewall zone, the unit policies are written between."""

    raw: FirewallZoneData

    @property
    def zone_id(self) -> str:
        """UUID used by policies to refer to the zone."""
        return self.raw["id"]

    @property
    def name(self) -> str:
        """Display name."""
        return self.raw["name"]

    @property
    def network_ids(self) -> list[str]:
        """UUIDs of the networks in the zone."""
        return self.raw["networkIds"]

    @property
    def origin(self) -> str:
        """`USER_DEFINED` or `SYSTEM_DEFINED`."""
        return self.raw["metadata"]["origin"]


class FirewallPolicyAction(TypedDict):
    """What happens to matched traffic."""

    type: str


class FirewallPolicyEndpoint(TypedDict):
    """Source or destination of a policy."""

    zoneId: str
    trafficFilter: NotRequired[dict[str, Any]]


class FirewallPolicyData(TypedDict):
    """One firewall policy; the list and detail endpoints return the same."""

    id: str
    name: str
    enabled: bool
    index: int
    action: FirewallPolicyAction
    source: FirewallPolicyEndpoint
    destination: FirewallPolicyEndpoint
    ipProtocolScope: dict[str, Any]
    loggingEnabled: bool
    metadata: EntityMetadata
    description: NotRequired[str]


class FirewallPolicy(ApiItem):
    """A firewall policy."""

    raw: FirewallPolicyData

    @property
    def policy_id(self) -> str:
        """UUID used in policy-scoped paths."""
        return self.raw["id"]

    @property
    def name(self) -> str:
        """Display name."""
        return self.raw["name"]

    @property
    def description(self) -> str | None:
        """Free text description."""
        return self.raw.get("description")

    @property
    def enabled(self) -> bool:
        """Whether the policy is enforced."""
        return self.raw["enabled"]

    @property
    def index(self) -> int:
        """Evaluation order; lower runs first."""
        return self.raw["index"]

    @property
    def action(self) -> str:
        """`ALLOW`, `BLOCK` or `REJECT`."""
        return self.raw["action"]["type"]

    @property
    def source_zone_id(self) -> str:
        """UUID of the zone traffic comes from."""
        return self.raw["source"]["zoneId"]

    @property
    def destination_zone_id(self) -> str:
        """UUID of the zone traffic goes to."""
        return self.raw["destination"]["zoneId"]

    @property
    def logging_enabled(self) -> bool:
        """Whether matches are sent to syslog."""
        return self.raw["loggingEnabled"]

    @property
    def origin(self) -> str:
        """`USER_DEFINED`, `SYSTEM_DEFINED` or `DERIVED`."""
        return self.raw["metadata"]["origin"]

    @property
    def predefined(self) -> bool:
        """Whether the console made the policy rather than a user."""
        return self.origin == "SYSTEM_DEFINED"
