"""DNS policies: local records and forwarded domains."""

from __future__ import annotations

from typing import NotRequired, TypedDict

from ....models.api import ApiItem
from .api import EntityMetadata


class DnsPolicyData(TypedDict):
    """One DNS policy.

    Every type has a `domain`; the other fields depend on the type, such as
    `ipv4Address` for an `A_RECORD` or `targetDomain` for a `CNAME_RECORD`.
    """

    id: str
    type: str
    enabled: bool
    metadata: EntityMetadata
    domain: NotRequired[str]


class DnsPolicy(ApiItem):
    """A DNS policy."""

    raw: DnsPolicyData

    @property
    def policy_id(self) -> str:
        """UUID used in policy-scoped paths."""
        return self.raw["id"]

    @property
    def type(self) -> str:
        """`A_RECORD`, `CNAME_RECORD`, `FORWARD_DOMAIN` and so on."""
        return self.raw["type"]

    @property
    def domain(self) -> str | None:
        """The domain the policy answers for."""
        return self.raw.get("domain")

    @property
    def enabled(self) -> bool:
        """Whether the policy is active."""
        return self.raw["enabled"]

    @property
    def origin(self) -> str:
        """Who made the policy."""
        return self.raw["metadata"]["origin"]
