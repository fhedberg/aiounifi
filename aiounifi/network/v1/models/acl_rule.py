"""ACL rules, the switch-enforced layer 2/3 rules."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict

from ....models.api import ApiItem
from .api import EntityMetadata


class AclRuleData(TypedDict):
    """One ACL rule; the list and detail endpoints return the same."""

    id: str
    type: str
    name: str
    enabled: bool
    action: str
    index: int
    metadata: EntityMetadata
    description: NotRequired[str]
    sourceFilter: NotRequired[dict[str, Any]]
    destinationFilter: NotRequired[dict[str, Any]]
    enforcingDeviceFilter: NotRequired[dict[str, Any]]


class AclRule(ApiItem):
    """An ACL rule."""

    raw: AclRuleData

    @property
    def rule_id(self) -> str:
        """UUID used in rule-scoped paths."""
        return self.raw["id"]

    @property
    def name(self) -> str:
        """Display name."""
        return self.raw["name"]

    @property
    def type(self) -> str:
        """`IPV4` or `MAC`."""
        return self.raw["type"]

    @property
    def enabled(self) -> bool:
        """Whether the rule is enforced."""
        return self.raw["enabled"]

    @property
    def action(self) -> str:
        """`ALLOW` or `BLOCK`."""
        return self.raw["action"]

    @property
    def index(self) -> int:
        """Evaluation order; lower runs first."""
        return self.raw["index"]

    @property
    def origin(self) -> str:
        """`USER_DEFINED` or `DERIVED`."""
        return self.raw["metadata"]["origin"]
