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


ValidNode = Union[Node, str]


class NodeCLI(DockerCLICaller):
    def update(
        self,
        node: ValidNode,
        availability: Optional[str] = None,
        labels_add: Dict[str, str] = {},
        rm_labels: List[str] = [],
        role: Optional[str] = None,
    ):
        full_cmd = self.docker_cmd + ["node", "update"]

        full_cmd.add_simple_arg("--availability", availability)
        for label_name, label_value in labels_add.items():
            full_cmd += ["--label-add", f"{label_name}={label_value}"]

        for label in rm_labels:
            full_cmd += ["--rm-label", label]

        full_cmd.add_simple_arg("--role", role)
        full_cmd.append(node)
        run(full_cmd)
