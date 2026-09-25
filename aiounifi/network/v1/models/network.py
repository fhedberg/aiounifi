"""Networks (VLANs) of a site."""

from __future__ import annotations

from typing import TypedDict

from ....models.api import ApiItem
from .api import EntityMetadata


class NetworkData(TypedDict):
    """One network, as returned by the list endpoint.

    The detail endpoint adds the DHCP, IPv4 and IPv6 settings.
    """

    id: str
    name: str
    enabled: bool
    default: bool
    management: str
    vlanId: int
    metadata: EntityMetadata


class Network(ApiItem):
    """A network."""

    raw: NetworkData

    @property
    def network_id(self) -> str:
        """UUID used in network-scoped paths."""
        return self.raw["id"]

    @property
    def name(self) -> str:
        """Display name."""
        return self.raw["name"]

    @property
    def enabled(self) -> bool:
        """Whether the network is enabled."""
        return self.raw["enabled"]

    @property
    def default(self) -> bool:
        """Whether this is the site's default network."""
        return self.raw["default"]

    @property
    def management(self) -> str:
        """`GATEWAY`, `SWITCH` or `UNMANAGED`."""
        return self.raw["management"]

    @property
    def vlan_id(self) -> int:
        """VLAN ID, 1 for the default network."""
        return self.raw["vlanId"]

    @property
    def origin(self) -> str:
        """Who made the network."""
        return self.raw["metadata"]["origin"]
