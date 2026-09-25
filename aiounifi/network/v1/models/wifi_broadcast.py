"""WiFi broadcasts, the SSIDs of a site."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict

from ....models.api import ApiItem
from .api import EntityMetadata

PERSONAL_SECURITY_TYPES = ("WPA2_PERSONAL", "WPA2_WPA3_PERSONAL", "WPA3_PERSONAL")


class WifiNetworkReference(TypedDict):
    """The network a broadcast puts its clients on.

    `NATIVE` means the default network; `SPECIFIC` carries a `networkId`.
    """

    type: str
    networkId: NotRequired[str]


class WifiSecurityConfiguration(TypedDict):
    """Security of a broadcast.

    The list endpoint returns the `type` only. The detail endpoint adds the
    `passphrase` of the personal types and the settings of the rest.
    """

    type: str
    passphrase: NotRequired[str]


class WifiBroadcastData(TypedDict):
    """One WiFi broadcast.

    The list endpoint returns the fields marked required here; the detail
    endpoint returns every field the console accepts back on update.
    """

    id: str
    type: str
    name: str
    enabled: bool
    metadata: EntityMetadata
    securityConfiguration: WifiSecurityConfiguration
    network: NotRequired[WifiNetworkReference]
    broadcastingDeviceFilter: NotRequired[dict[str, Any]]
    hideName: NotRequired[bool]
    clientIsolationEnabled: NotRequired[bool]


class WifiBroadcast(ApiItem):
    """A WiFi broadcast."""

    raw: WifiBroadcastData

    @property
    def broadcast_id(self) -> str:
        """UUID used in broadcast-scoped paths."""
        return self.raw["id"]

    @property
    def name(self) -> str:
        """SSID."""
        return self.raw["name"]

    @property
    def type(self) -> str:
        """`STANDARD` or `IOT_OPTIMIZED`."""
        return self.raw["type"]

    @property
    def enabled(self) -> bool:
        """Whether the SSID is broadcast."""
        return self.raw["enabled"]

    @property
    def origin(self) -> str:
        """Who made the broadcast."""
        return self.raw["metadata"]["origin"]

    @property
    def security_type(self) -> str:
        """`OPEN`, `WPA2_PERSONAL`, `WPA3_ENTERPRISE` and so on."""
        return self.raw["securityConfiguration"]["type"]

    @property
    def passphrase(self) -> str | None:
        """Passphrase of a personal network; only the detail endpoint has it."""
        return self.raw["securityConfiguration"].get("passphrase")

    @property
    def hide_name(self) -> bool | None:
        """Whether the SSID is hidden; only the detail endpoint has it."""
        return self.raw.get("hideName")

    @property
    def network_id(self) -> str | None:
        """UUID of the network, `None` for the default network."""
        return self.raw.get("network", {}).get("networkId")
