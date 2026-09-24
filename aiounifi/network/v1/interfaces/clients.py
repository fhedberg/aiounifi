"""Connected clients."""

from __future__ import annotations

from typing import cast

from ..api_handlers import APIHandler
from ..models.client import (
    Client,
    ClientActionRequest,
    ClientActionResponse,
    GetClientRequest,
    ListClientsRequest,
    normalize_mac,
)


class Clients(APIHandler[Client]):
    """Clients connected to the active site, keyed by MAC address.

    VPN and Teleport clients have no MAC address, so `update` leaves them out
    of the cache; `list_page` still returns them.
    """

    item_cls = Client
    obj_id_key = "macAddress"

    def normalize_obj_id(self, obj_id: str) -> str:
        """Canonical MAC address."""
        return normalize_mac(obj_id)

    def list_request(self, offset: int, limit: int) -> ListClientsRequest:
        """Return the list request for one page."""
        return ListClientsRequest.create(self.api_client.site_id, offset, limit)

    async def list_page(
        self,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> list[Client]:
        """Return one page of clients without touching the cache."""
        response = await self.api_client.request(
            ListClientsRequest.create(
                self.api_client.site_id, offset, limit, filter_value
            )
        )
        return [Client(raw) for raw in response["data"]]

    async def get_details(self, client_id: str) -> Client:
        """Fetch one client."""
        response = await self.api_client.request(
            GetClientRequest.create(self.api_client.site_id, client_id)
        )
        return Client(response["data"][0])

    async def get_by_mac(self, mac_address: str) -> Client | None:
        """Look a client up by MAC address, filtered on the console."""
        clients = await self.list_page(
            limit=1, filter_value=f"macAddress.eq('{normalize_mac(mac_address)}')"
        )
        return clients[0] if clients else None

    async def authorize_guest_access(
        self,
        client_id: str,
        time_limit_minutes: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> ClientActionResponse:
        """Authorize a guest client, with optional time, data and rate limits."""
        response = await self.api_client.request(
            ClientActionRequest.create_authorize_guest_access(
                self.api_client.site_id,
                client_id,
                time_limit_minutes,
                data_usage_limit_mbytes,
                rx_rate_limit_kbps,
                tx_rate_limit_kbps,
            )
        )
        return cast("ClientActionResponse", response["data"][0])

    async def unauthorize_guest_access(self, client_id: str) -> ClientActionResponse:
        """Revoke a guest client's authorization."""
        response = await self.api_client.request(
            ClientActionRequest.create_unauthorize_guest_access(
                self.api_client.site_id, client_id
            )
        )
        return cast("ClientActionResponse", response["data"][0])
