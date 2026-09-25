"""WiFi broadcasts."""

from __future__ import annotations

from ....errors import RequestError
from ....models.wlan import wlan_qr_code
from ..api_handlers import ConfigurationHandler
from ..models.wifi_broadcast import PERSONAL_SECURITY_TYPES, WifiBroadcast


class WifiBroadcasts(ConfigurationHandler[WifiBroadcast]):
    """The SSIDs of the active site, keyed by UUID.

    The list endpoint leaves out the passphrase and most settings; they come
    from `get_details`, which also refreshes the cached item.
    """

    item_cls = WifiBroadcast
    collection = "wifi/broadcasts"

    async def set_passphrase(self, broadcast_id: str, passphrase: str) -> WifiBroadcast:
        """Change the passphrase of a personal (pre-shared key) network."""
        details = await self.get_details(broadcast_id)
        if details.security_type not in PERSONAL_SECURITY_TYPES:
            raise RequestError(
                f"WiFi broadcast {details.name!r} is {details.security_type}, "
                "which has no passphrase"
            )
        security = {**details.raw["securityConfiguration"], "passphrase": passphrase}
        return await self.update_item(broadcast_id, {"securityConfiguration": security})

    async def generate_qr_code(
        self,
        broadcast_id: str,
        dark: str | None = None,
        light: str | None = None,
        border: int | None = None,
    ) -> bytes:
        """Return a PNG QR code that joins the network.

        Fetches the details, since only they carry the passphrase.
        """
        details = await self.get_details(broadcast_id)
        return wlan_qr_code(
            details.name,
            details.passphrase,
            hidden=details.hide_name is True,
            dark=dark,
            light=light,
            border=border,
        )
