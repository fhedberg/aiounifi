"""Networks."""

from __future__ import annotations

from ..api_handlers import ConfigurationHandler
from ..models.network import Network


class Networks(ConfigurationHandler[Network]):
    """The networks (VLANs) of the active site, keyed by UUID."""

    item_cls = Network
    collection = "networks"
    read_only_keys = ("id", "metadata", "default")
