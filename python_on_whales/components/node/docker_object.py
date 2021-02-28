from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import python_on_whales.components.task
from python_on_whales.client_config import ClientConfig, ReloadableObjectFromJson
from python_on_whales.components.node.cli_wrapper import NodeCLI
from python_on_whales.components.node.models import (
    NodeDescription,
    NodeInspectResult,
    NodeManagerStatus,
    NodeSpec,
    NodeStatus,
    NodeVersion,
)
from python_on_whales.utils import run


class Node(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["node", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> NodeInspectResult:
        return NodeInspectResult.parse_obj(json_object)

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

    def ps(self) -> List[python_on_whales.components.task.Task]:
        """Returns the list of tasks running on this node

        # Returns
            A `List[python_on_whales.Task]` object.

        """
        return NodeCLI(self.client_config).ps(self)


ValidNode = Union[Node, str]
