from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import python_on_whales.components.service.cli_wrapper
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.task.models import (
    AssignedGenericResources,
    ObjectVersion,
    TaskInspectResult,
    TaskSpec,
    TaskStatus,
)
from python_on_whales.utils import run


class Task(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> TaskInspectResult:
        return TaskInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> TaskInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def version(self) -> ObjectVersion:
        return self._get_inspect_result().version

    @property
    def created_at(self) -> datetime:
        return self._get_inspect_result().created_at

    @property
    def updated_at(self) -> datetime:
        return self._get_inspect_result().updated_at

    @property
    def name(self) -> Optional[str]:
        return self._get_inspect_result().name

    @property
    def labels(self) -> Dict[str, str]:
        return self._get_inspect_result().labels

    @property
    def spec(self) -> TaskSpec:
        return self._get_inspect_result().spec

    @property
    def service_id(self) -> str:
        return self._get_inspect_result().service_id

    @property
    def slot(self) -> Optional[int]:
        return self._get_inspect_result().slot

    @property
    def node_id(self) -> str:
        return self._get_inspect_result().node_id

    @property
    def assigned_generic_resources(self) -> Optional[List[AssignedGenericResources]]:
        return self._get_inspect_result().assigned_generic_resources

    @property
    def status(self) -> TaskStatus:
        return self._get_inspect_result().status

    @property
    def desired_state(self) -> str:
        return self._get_inspect_result().desired_state


class TaskCLI(DockerCLICaller):
    def list(self) -> List[Task]:
        """Returns all tasks in the swarm

        # Returns
            `List[python_on_whales.Task]`
        """
        service_cli = python_on_whales.components.service.cli_wrapper.ServiceCLI(
            self.client_config
        )
        return service_cli.ps(service_cli.list())

    def inspect(self, x: Union[str, List[str]]) -> Union[Task, List[Task]]:
        """Returns a `python_on_whales.Task` object from its ID."""
        if isinstance(x, str):
            return Task(self.client_config, x)
        else:
            return [Task(self.client_config, reference) for reference in x]

    def logs(self):
        """Not Yet implemented"""
        raise NotImplementedError
