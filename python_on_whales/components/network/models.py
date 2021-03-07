from datetime import datetime
from typing import Any, Dict, List, Optional

from python_on_whales.utils import DockerCamelModel


class NetworkIPAM(DockerCamelModel):
    driver: str
    config: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]]


class NetworkContainer(DockerCamelModel):
    name: str
    endpoint_id: str
    mac_address: str
    ipv4_address: str
    ipv6_address: str


class NetworkInspectResult(DockerCamelModel):
    name: str
    id: str
    created: datetime
    scope: str
    driver: str
    enable_ipv6: bool
    ipam: NetworkIPAM
    internal: bool
    attachable: bool
    ingress: bool
    containers: Dict[str, NetworkContainer]
    options: Dict[str, Any]
    labels: Dict[str, str]
    config_from: Optional[dict]
    config_only: Optional[bool]
