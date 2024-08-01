from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, overload

import python_on_whales.components.task.cli_wrapper
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.node.models import (
    NodeDescription,
    NodeInspectResult,
    NodeManagerStatus,
    NodeSpec,
    NodeStatus,
    NodeVersion,
)
from python_on_whales.utils import run, to_list


class Node(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        json_str = run(self.docker_cmd + ["node", "inspect", reference])
        return json.loads(json_str)[0]

    def _parse_json_object(self, json_object: Dict[str, Any]) -> NodeInspectResult:
        return NodeInspectResult(**json_object)

    def _get_inspect_result(self) -> NodeInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

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

    def __repr__(self):
        return f"python_on_whales.Node(id='{self.id[:12]}', hostname='{self.description.hostname}', role='{self.spec.role}')"

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

    def ps(self) -> List[python_on_whales.components.task.cli_wrapper.Task]:
        """Returns the list of tasks running on this node

        # Returns
            A `List[python_on_whales.Task]` object.

        """
        return NodeCLI(self.client_config).ps(self)


ValidNode = Union[Node, str]


class NodeCLI(DockerCLICaller):
    def demote(self, x: Union[ValidNode, List[ValidNode]]):
        """Demote one or more nodes from manager in the swarm

        Parameters:
            x: One or a list of nodes.
        """
        full_cmd = self.docker_cmd + ["node", "demote"]
        if x == []:
            return
        full_cmd += to_list(x)
        run(full_cmd)

    @overload
    def inspect(self, x: str) -> Node: ...

    @overload
    def inspect(self, x: List[str]) -> List[Node]: ...

    def inspect(self, x: Union[str, List[str]]) -> Union[Node, List[Node]]:
        """Returns a `python_on_whales.Node` object from a string
        (id or hostname of the node)

        Parameters:
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

        Parameters:
            x: One or a list of nodes.
        """
        full_cmd = self.docker_cmd + ["node", "promote"]
        if x == []:
            return
        full_cmd += to_list(x)
        run(full_cmd)

    def ps(
        self, x: Union[ValidNode, List[ValidNode], None] = None
    ) -> List[python_on_whales.components.task.cli_wrapper.Task]:
        """Returns the list of swarm tasks running on one or more nodes.

        ```python
        from python_on_whales import docker

        tasks = docker.node.ps("my-node-name")
        print(tasks[0].desired_state)
        # running
        ```

        Parameters:
            x: One or more nodes (can be id, name or `python_on_whales.Node` object.).
                If the argument is not provided, it defaults to the current node.
                An empty list means an empty list will also be returned.

        # Returns
            `List[python_on_whales.Task]`
        """
        if x == []:
            return []
        elif x is None:
            # this is the default, on the command line, nothing is provided, and then
            # it automatically defaults to the current node.
            command_args = []
        else:
            command_args = to_list(x)
        full_cmd = (
            self.docker_cmd + ["node", "ps", "--quiet", "--no-trunc"] + command_args
        )
        ids = run(full_cmd).splitlines()
        return [
            python_on_whales.components.task.cli_wrapper.Task(
                self.client_config, id_, is_immutable_id=True
            )
            for id_ in ids
        ]

    def remove(self, x: Union[ValidNode, List[ValidNode]], force: bool = False):
        """Remove one or more nodes from the swarm

        Parameters:
            x: One node or a list of nodes. You can use the id or the hostname of a node.
                You can also use a `python_on_whales.Node`.
            force: Force remove a node from the swarm
        """
        full_cmd = self.docker_cmd + ["node", "remove"]
        full_cmd.add_flag("--force", force)
        if x == []:
            return
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

        Parameters:
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
            full_cmd += ["--label-rm", label]

        full_cmd.add_simple_arg("--role", role)
        full_cmd.append(node)
        run(full_cmd)
