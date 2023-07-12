from datetime import datetime
from typing import Any, Dict, List, Optional

from python_on_whales.utils import DockerCamelModel


class NetworkIPAM(DockerCamelModel):
    driver: Optional[str] = None
    config: Optional[List[Dict[str, Any]]] = None
    options: Optional[Dict[str, Any]] = None


class NetworkContainer(DockerCamelModel):
    name: Optional[str] = None
    endpoint_id: Optional[str] = None
    mac_address: Optional[str] = None
    ipv4_address: Optional[str] = None
    ipv6_address: Optional[str] = None


class NetworkInspectResult(DockerCamelModel):
    name: Optional[str] = None
    id: Optional[str] = None
    created: Optional[datetime] = None
    scope: Optional[str] = None
    driver: Optional[str] = None
    enable_ipv6: Optional[bool] = None
    ipam: Optional[NetworkIPAM] = None
    internal: Optional[bool] = None
    attachable: Optional[bool] = None
    ingress: Optional[bool] = None
    containers: Optional[Dict[str, NetworkContainer]] = None
    options: Optional[Dict[str, Any]] = None
    labels: Optional[Dict[str, str]] = None
    config_from: Optional[dict] = None
    config_only: Optional[bool] = None
