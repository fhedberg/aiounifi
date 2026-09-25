"""Resource interfaces of the Network API v1."""

from .acl_rules import AclRules
from .clients import Clients
from .devices import Devices
from .dns_policies import DnsPolicies
from .firewall import FirewallPolicies, FirewallZones
from .networks import Networks
from .sites import Sites
from .vouchers import Vouchers
from .wifi_broadcasts import WifiBroadcasts

__all__ = [
    "AclRules",
    "Clients",
    "Devices",
    "DnsPolicies",
    "FirewallPolicies",
    "FirewallZones",
    "Networks",
    "Sites",
    "Vouchers",
    "WifiBroadcasts",
]
