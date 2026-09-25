"""DNS policies."""

from __future__ import annotations

from ..api_handlers import ConfigurationHandler
from ..models.dns_policy import DnsPolicy


class DnsPolicies(ConfigurationHandler[DnsPolicy]):
    """The DNS policies of the active site, keyed by UUID."""

    item_cls = DnsPolicy
    collection = "dns/policies"
