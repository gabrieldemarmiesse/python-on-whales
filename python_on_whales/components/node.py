from typing import Any, Dict, List, Optional, Union

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import DockerCamelModel, run


class NodeInspectResult(DockerCamelModel):
    ID: str
    version: dict


class Node(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "ID", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["node", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> NodeInspectResult:
        return NodeInspectResult.parse_obj(json_object)

    @property
    def id(self) -> str:
        return self._get_immutable_id()

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
    def demote(self):
        """Not yet implemented"""
        raise NotImplementedError

    def inspect(self):
        """Not yet implemented"""
        raise NotImplementedError

    def list(self):
        """Not yet implemented"""
        raise NotImplementedError

    def promote(self):
        """Not yet implemented"""
        raise NotImplementedError

    def ps(self):
        """Not yet implemented"""
        raise NotImplementedError

    def remove(self):
        """Not yet implemented"""
        raise NotImplementedError

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
