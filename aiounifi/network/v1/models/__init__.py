"""Models of the Network API v1."""

from .acl_rule import AclRule, AclRuleData
from .api import ApiErrorResponse, ApiRequest, ApiResponse, EntityMetadata
from .client import Client, ClientData, normalize_mac
from .device import Device, DeviceData, DevicePort, DeviceRadio, DeviceStatistics
from .dns_policy import DnsPolicy, DnsPolicyData
from .firewall import (
    FirewallPolicy,
    FirewallPolicyData,
    FirewallZone,
    FirewallZoneData,
)
from .info import InfoData
from .network import Network, NetworkData
from .site import Site, SiteData
from .voucher import Voucher, VoucherData
from .wifi_broadcast import WifiBroadcast, WifiBroadcastData

__all__ = [
    "AclRule",
    "AclRuleData",
    "ApiErrorResponse",
    "ApiRequest",
    "ApiResponse",
    "Client",
    "ClientData",
    "Device",
    "DeviceData",
    "DevicePort",
    "DeviceRadio",
    "DeviceStatistics",
    "DnsPolicy",
    "DnsPolicyData",
    "EntityMetadata",
    "FirewallPolicy",
    "FirewallPolicyData",
    "FirewallZone",
    "FirewallZoneData",
    "InfoData",
    "Network",
    "NetworkData",
    "Site",
    "SiteData",
    "Voucher",
    "VoucherData",
    "WifiBroadcast",
    "WifiBroadcastData",
    "normalize_mac",
]
