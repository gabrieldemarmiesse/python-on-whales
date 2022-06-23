import json
from typing import Dict, List

from python_on_whales.client_config import DockerCLICaller
from python_on_whales.components.system.models import (
    DockerEvent,
    DockerItemsSummary,
    SystemInfo,
)
from python_on_whales.utils import format_dict_for_cli, run


class DiskFreeResult:
    def __init__(self, cli_stdout: str):
        docker_items = {}
        for line in cli_stdout.splitlines():
            docker_items_dict = json.loads(line)
            reclamable = docker_items_dict["Reclaimable"]
            docker_items_dict["Reclaimable"] = reclamable.split(" ")[0]
            if "%" in reclamable:
                docker_items_dict["ReclaimablePercent"] = reclamable.split(" ")[1][1:-2]
            else:
                docker_items_dict["ReclaimablePercent"] = "100"

            docker_items[docker_items_dict["Type"]] = docker_items_dict

        self.images: DockerItemsSummary
        self.images = DockerItemsSummary.parse_obj(docker_items["Images"])
        self.containers: DockerItemsSummary
        self.containers = DockerItemsSummary.parse_obj(docker_items["Containers"])
        self.volumes: DockerItemsSummary
        self.volumes = DockerItemsSummary.parse_obj(docker_items["Local Volumes"])
        self.build_cache: DockerItemsSummary
        self.build_cache = DockerItemsSummary.parse_obj(docker_items["Build Cache"])


class SystemCLI(DockerCLICaller):
    def disk_free(self) -> DiskFreeResult:
        """Give information about the disk usage of the Docker daemon.

        Returns a `python_on_whales.DiskFreeResult` object.

        ```python
        from python_on_whales import docker
        disk_free_result = docker.system.disk_free()
        print(disk_free_result.images.active)  #int
        print(disk_free_result.containers.reclaimable)  # int, number of bytes
        print(disk_free_result.volumes.reclaimable_percent)  # float
        print(disk_free_result.build_cache.total_count)  # int
        print(disk_free_result.build_cache.size)  # int, number of bytes
        ...
        ```
        Note that the number are not 100% accurate because the docker CLI
        doesn't provide the exact numbers.

        Maybe in a future implementation, we can provide exact numbers.

        Verbose mode is not yet implemented.
        """

        full_cmd = self.docker_cmd + ["system", "df", "--format", "{{json .}}"]
        return DiskFreeResult(run(full_cmd))

    def events(self, filters:List[str]) -> List[DockerEvent]:
        """Returns docker events information up to the current point in time.

        # Arguments
            filters: See the [Docker documentation page about filtering
                ](https://docs.docker.com/engine/reference/commandline/events/#filtering).

        # Returns
            A list of `python_on_whales.DockerEvent` objects

        Currently only supports filters and adds a default option of `--until "0s"`. The
        until option forces the events command to return with all the events upto the
        current point in time. Without this option, a call to events would listen for
        events indefinitely.
        [reference page for
        system events](https://docs.docker.com/engine/api/v1.40/#operation/SystemEvents)
        """
        full_cmd = self.docker_cmd + ["system", "events", "--format", "{{json .}}", "--until", "0s"]
        for filter in filters:
            full_cmd.extend(["--filter", filter])
        event_strings = run(full_cmd).split()
        events = []
        for event in event_strings:
            parsed = DockerEvent.parse_raw(event)
            events.append(parsed)
        return events

    def info(self) -> SystemInfo:
        """Returns diverse information about the Docker client and daemon.

        # Returns
            A `python_on_whales.SystemInfo` object

        As an example

        ```python
        from python_on_whales import docker

        info = docker.system.info()
        print(info.images)
        # 40
        print(info.plugins.volume)
        # ["local"}
        ...
        ```

        You can find all attributes available by looking up the [reference page for
        system info](https://docs.docker.com/engine/api/v1.40/#operation/SystemInfo).
        """
        full_cmd = self.docker_cmd + ["system", "info", "--format", "{{json .}}"]
        return SystemInfo.parse_raw(run(full_cmd))

    def prune(
        self, all: bool = False, volumes: bool = False, filters: Dict[str, str] = {}
    ) -> None:
        """Remove unused docker data

        # Arguments
            all: Remove all unused images not just dangling ones
            volumes: Prune volumes
            filters: See the [Docker documentation page about filtering
                ](https://docs.docker.com/engine/reference/commandline/system_prune/#filtering).
                For example, `filters=dict(until="24h")`.
        """
        full_cmd = self.docker_cmd + ["system", "prune", "--force"]
        full_cmd.add_flag("--all", all)
        full_cmd.add_flag("--volumes", volumes)
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))
        run(full_cmd)
