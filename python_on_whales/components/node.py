from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, overload

from pydantic import Field

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import DockerCamelModel, run, to_list


class NodeVersion(DockerCamelModel):
    index: int


class NodeSpec(DockerCamelModel):
    name: Optional[str]
    labels: Dict[str, str]
    role: str
    availability: str


class NodePlatform(DockerCamelModel):
    architecture: str
    os: str = Field(alias="OS")


class NodeNamedResourceSpec(DockerCamelModel):
    kind: str
    value: str


class NodeDiscreteResourceSpec(DockerCamelModel):
    kind: str
    value: int


class NodeGenericResource(DockerCamelModel):
    named_resource_spec: Optional[NodeNamedResourceSpec]
    discrete_resource_spec: Optional[NodeDiscreteResourceSpec]


class NodeResource(DockerCamelModel):
    nano_cpus: int = Field(alias="NanoCPUs")
    memory_bytes: int
    generic_resources: Optional[List[NodeGenericResource]]


class EnginePlugin(DockerCamelModel):
    type: str
    name: str


class NodeEngine(DockerCamelModel):
    engine_version: str
    labels: Optional[Dict[str, str]]
    plugins: List[EnginePlugin]


class NodeTLSInfo(DockerCamelModel):
    trust_root: str
    cert_issuer_subject: str
    cert_issuer_public_key: str


class NodeDescription(DockerCamelModel):
    hostname: str
    platform: NodePlatform
    resources: NodeResource
    engine: NodeEngine
    tls_info: NodeTLSInfo


class NodeStatus(DockerCamelModel):
    state: str
    message: Optional[str]
    addr: str


class NodeManagerStatus(DockerCamelModel):
    leader: bool
    reachability: str
    addr: str


class NodeInspectResult(DockerCamelModel):
    id: str = Field(alias="ID")
    version: NodeVersion
    created_at: datetime
    updated_at: datetime
    spec: NodeSpec
    description: NodeDescription
    status: NodeStatus
    manager_status: Optional[NodeManagerStatus]


class Node(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["node", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> NodeInspectResult:
        return NodeInspectResult.parse_obj(json_object)

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def version(self) -> NodeVersion:
        return self._get_inspect_result().version

    @property
    def created_at(self) -> datetime:
        return self._get_inspect_result().created_at

    @property
    def updated_at(self) -> datetime:
        return self._get_inspect_result().updated_at

    @property
    def spec(self) -> NodeSpec:
        return self._get_inspect_result().spec

    @property
    def description(self) -> NodeDescription:
        return self._get_inspect_result().description

    @property
    def status(self) -> NodeStatus:
        return self._get_inspect_result().status

    @property
    def manager_status(self) -> Optional[NodeManagerStatus]:
        return self._get_inspect_result().manager_status

    def update(
        self,
        availability: Optional[str] = None,
        labels_add: Dict[str, str] = {},
        rm_labels: List[str] = [],
        role: Optional[str] = None,
    ) -> None:
        """Updates this Swarm node.

        See [`docker.node.update`](../sub-commands/node.md#update) for more information
        about the arguments.
        """
        NodeCLI(self.client_config).update(
            self, availability, labels_add, rm_labels, role
        )


ValidNode = Union[Node, str]


class NodeCLI(DockerCLICaller):
    def demote(self, x: Union[ValidNode, List[ValidNode]]):
        """Demote one or more nodes from manager in the swarm

        # Arguments
            x: One or a list of nodes.
        """
        full_cmd = self.docker_cmd + ["node", "demote"]
        full_cmd += to_list(x)
        run(full_cmd)

    @overload
    def inspect(self, x: str) -> Node:
        ...

    @overload
    def inspect(self, x: List[str]) -> List[Node]:
        ...

    def inspect(self, x: Union[str, List[str]]) -> Union[Node, List[Node]]:
        """Returns a `python_on_whales.Node` object from a string
        (id or hostname of the node)

        # Arguments
            x: One id or hostname or a list of ids or hostnames

        # Returns
            One or a list of `python_on_whales.Node`
        """
        if isinstance(x, str):
            return Node(self.client_config, x)
        else:
            return [Node(self.client_config, reference) for reference in x]

    def list(self) -> List[Node]:
        """Returns the list of nodes in this swarm.

        # Returns
            A `List[python_on_whales.Node]`
        """
        full_cmd = self.docker_cmd + ["node", "list", "--quiet"]
        all_ids = run(full_cmd).splitlines()
        return [Node(self.client_config, x, is_immutable_id=True) for x in all_ids]

    def promote(self, x: Union[ValidNode, List[ValidNode]]):
        """Promote one or more nodes to manager in the swarm

        # Arguments
            x: One or a list of nodes.
        """
        full_cmd = self.docker_cmd + ["node", "promote"]
        full_cmd += to_list(x)
        run(full_cmd)

    def ps(self):
        """Not yet implemented"""
        raise NotImplementedError

    def remove(self, x: Union[ValidNode, List[ValidNode]], force: bool = False):
        """Remove one or more nodes from the swarm

        # Arguments
            x: One node or a list of nodes. You can use the id or the hostname of a node.
                You can also use a `python_on_whales.Node`.
            force: Force remove a node from the swarm
        """
        full_cmd = self.docker_cmd + ["node", "remove"]
        full_cmd.add_flag("--force", force)
        full_cmd += to_list(x)
        run(full_cmd)

    def update(
        self,
        node: ValidNode,
        availability: Optional[str] = None,
        labels_add: Dict[str, str] = {},
        rm_labels: List[str] = [],
        role: Optional[str] = None,
    ) -> None:
        """Updates a Swarm node.

        # Arguments
            node: The node to update, you can use a string or a `python_on_whales.Node`
                object.
            availability: Availability of the node ("active"|"pause"|"drain")
            labels_add: Remove a node label if exists
            rm_labels: Labels to remove from the node.
            role: Role of the node ("worker"|"manager")
        """
        full_cmd = self.docker_cmd + ["node", "update"]

        full_cmd.add_simple_arg("--availability", availability)
        for label_name, label_value in labels_add.items():
            full_cmd += ["--label-add", f"{label_name}={label_value}"]

        for label in rm_labels:
            full_cmd += ["--rm-label", label]

        full_cmd.add_simple_arg("--role", role)
        full_cmd.append(node)
        run(full_cmd)
