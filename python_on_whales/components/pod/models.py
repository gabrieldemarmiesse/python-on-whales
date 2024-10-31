from datetime import datetime
from typing import List, Mapping, Optional

import pydantic
from pydantic import AliasChoices
from typing_extensions import Annotated

from python_on_whales.components.container.models import PortBinding
from python_on_whales.utils import DockerCamelModel


class PodInfraConfig(DockerCamelModel):
    port_bindings: Optional[Mapping[str, Optional[List[PortBinding]]]] = None
    host_network: Optional[bool] = None
    static_ip: Optional[str] = None
    static_mac: Optional[str] = None
    no_manage_resolv_conf: Optional[bool] = None
    dns_server: Optional[List[str]] = None
    dns_search: Optional[List[str]] = None
    dns_option: Optional[List[str]] = None
    no_manage_hosts: Optional[bool] = None
    host_add: Optional[List[str]] = None
    networks: Optional[List[str]] = None
    network_options: Optional[List[str]] = None
    pid_ns: Optional[str] = None
    userns: Optional[str] = None
    uts_ns: Optional[str] = None


class PodContainer(DockerCamelModel):
    id: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None


class PodInspectResult(DockerCamelModel):
    id: Optional[str] = None
    name: Optional[str] = None
    created: Annotated[
        Optional[datetime],
        pydantic.Field(validation_alias=AliasChoices("Created", "CreatedAt")),
    ] = None
    create_command: Optional[List[str]] = None
    exit_policy: Optional[str] = None
    state: Optional[str] = None
    hostname: Optional[str] = None
    labels: Optional[Mapping[str, str]] = None
    create_cgroup: Optional[bool] = None
    cgroup_parent: Optional[str] = None
    cgroup_path: Optional[str] = None
    create_infra: Optional[bool] = None
    infra_container_id: Optional[str] = None
    infra_config: Optional[PodInfraConfig] = None
    shared_namespaces: Optional[List[str]] = None
    num_containers: Optional[int] = None
    containers: Optional[List[PodContainer]] = None
