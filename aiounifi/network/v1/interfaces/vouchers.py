"""Hotspot vouchers."""

from __future__ import annotations

from typing import Any

from ....interfaces.api_handlers import ItemEvent
from ..api_handlers import SiteResourceHandler
from ..models.api import SiteResourceRequest
from ..models.voucher import Voucher


class Vouchers(SiteResourceHandler[Voucher]):
    """The hotspot vouchers of the active site, keyed by UUID.

    Vouchers cannot be edited, only generated and deleted.
    """

    item_cls = Voucher
    collection = "hotspot/vouchers"

    async def generate(
        self,
        name: str,
        time_limit_minutes: int,
        count: int = 1,
        authorized_guest_limit: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> list[Voucher]:
        """Generate vouchers and add them to the cache."""
        data: dict[str, Any] = {
            "name": name,
            "timeLimitMinutes": time_limit_minutes,
            "count": count,
        }
        if authorized_guest_limit is not None:
            data["authorizedGuestLimit"] = authorized_guest_limit
        if data_usage_limit_mbytes is not None:
            data["dataUsageLimitMBytes"] = data_usage_limit_mbytes
        if rx_rate_limit_kbps is not None:
            data["rxRateLimitKbps"] = rx_rate_limit_kbps
        if tx_rate_limit_kbps is not None:
            data["txRateLimitKbps"] = tx_rate_limit_kbps
        response = await self.api_client.request(
            SiteResourceRequest.create_post(
                self.api_client.site_id, self.collection, data
            )
        )
        raw_vouchers = response["data"][0].get("vouchers", [])
        for raw in raw_vouchers:
            self.process_item(raw)
        return [Voucher(raw) for raw in raw_vouchers]

    async def delete(self, voucher_id: str) -> None:
        """Delete one voucher."""
        await self.api_client.request(
            SiteResourceRequest.create_delete(
                self.api_client.site_id, self.collection, voucher_id
            )
        )
        self._forget(voucher_id)

    async def delete_matching(self, filter_value: str) -> int:
        """Delete every voucher matching a filter, such as `expired.eq(true)`.

        Returns how many were deleted. The cache is refreshed afterwards,
        since the console does not say which ones went.
        """
        response = await self.api_client.request(
            SiteResourceRequest.create_delete(
                self.api_client.site_id, self.collection, filter_value=filter_value
            )
        )
        await self.update()
        return int(response["data"][0].get("vouchersDeleted", 0))

    def _forget(self, voucher_id: str) -> None:
        """Drop a voucher from the cache and tell subscribers."""
        if self._items.pop(voucher_id, None) is not None:
            self.signal_subscribers(ItemEvent.DELETED, voucher_id)
