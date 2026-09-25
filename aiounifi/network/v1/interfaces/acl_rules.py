"""ACL rules."""

from __future__ import annotations

from ..api_handlers import ConfigurationHandler
from ..models.acl_rule import AclRule


class AclRules(ConfigurationHandler[AclRule]):
    """The ACL rules of the active site, keyed by UUID."""

    item_cls = AclRule
    collection = "acl-rules"
    read_only_keys = ("id", "metadata", "index")
