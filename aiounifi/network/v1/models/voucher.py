"""Hotspot vouchers."""

from __future__ import annotations

from typing import NotRequired, TypedDict

from ....models.api import ApiItem


class VoucherData(TypedDict):
    """One hotspot voucher."""

    id: str
    code: str
    name: str
    createdAt: str
    expired: bool
    timeLimitMinutes: int
    authorizedGuestCount: int
    authorizedGuestLimit: NotRequired[int]
    activatedAt: NotRequired[str]
    expiresAt: NotRequired[str]
    dataUsageLimitMBytes: NotRequired[int]
    rxRateLimitKbps: NotRequired[int]
    txRateLimitKbps: NotRequired[int]


class Voucher(ApiItem):
    """A hotspot voucher."""

    raw: VoucherData

    @property
    def voucher_id(self) -> str:
        """UUID used in voucher-scoped paths."""
        return self.raw["id"]

    @property
    def code(self) -> str:
        """The code a guest types into the hotspot portal."""
        return self.raw["code"]

    @property
    def name(self) -> str:
        """Note shared by every voucher generated in the same batch."""
        return self.raw["name"]

    @property
    def created_at(self) -> str:
        """When the voucher was generated, ISO 8601."""
        return self.raw["createdAt"]

    @property
    def activated_at(self) -> str | None:
        """When a guest first used the voucher, ISO 8601."""
        return self.raw.get("activatedAt")

    @property
    def expires_at(self) -> str | None:
        """When the voucher stops working, ISO 8601; set once activated."""
        return self.raw.get("expiresAt")

    @property
    def expired(self) -> bool:
        """Whether the voucher can no longer be used."""
        return self.raw["expired"]

    @property
    def time_limit_minutes(self) -> int:
        """How long access lasts once activated."""
        return self.raw["timeLimitMinutes"]

    @property
    def authorized_guest_count(self) -> int:
        """How many guests have used the voucher."""
        return self.raw["authorizedGuestCount"]

    @property
    def authorized_guest_limit(self) -> int | None:
        """How many guests may use the voucher; `None` is unlimited."""
        return self.raw.get("authorizedGuestLimit")

    @property
    def data_usage_limit_mbytes(self) -> int | None:
        """Data cap per guest."""
        return self.raw.get("dataUsageLimitMBytes")

    @property
    def rx_rate_limit_kbps(self) -> int | None:
        """Download rate cap."""
        return self.raw.get("rxRateLimitKbps")

    @property
    def tx_rate_limit_kbps(self) -> int | None:
        """Upload rate cap."""
        return self.raw.get("txRateLimitKbps")
