import json
import shutil
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from python_on_whales.download_binaries import DOCKER_BINARY_PATH, download_docker_cli
from python_on_whales.utils import to_list

from .utils import ValidPath, run

CACHE_VALIDITY_PERIOD = 0.01


class Command(list):
    def add_simple_arg(self, name: str, value: Any):
        if value is not None:
            self.extend([name, value])

    def add_flag(self, name: str, value: bool):
        if value:
            self.append(name)

    def add_args_list(self, arg_name: str, list_values: list):
        for value in to_list(list_values):
            self.extend([arg_name, value])

    def __add__(self, other) -> "Command":
        return Command(super().__add__(other))


@dataclass
class ClientConfig:

    config: Optional[ValidPath] = None
    context: Optional[str] = None
    debug: Optional[bool] = None
    host: Optional[str] = None
    log_level: Optional[str] = None
    tls: Optional[bool] = None
    tlscacert: Optional[ValidPath] = None
    tlscert: Optional[ValidPath] = None
    tlskey: Optional[ValidPath] = None
    tlsverify: Optional[bool] = None
    client_binary_path: Optional[ValidPath] = None

    def get_docker_path(self) -> ValidPath:
        if self.client_binary_path is None:
            docker_sys = shutil.which("docker")
            if docker_sys is not None:
                self.client_binary_path = docker_sys
            elif DOCKER_BINARY_PATH.exists():
                self.client_binary_path = DOCKER_BINARY_PATH
            else:
                warnings.warn(
                    "The docker client binary file was not found on your system. \n"
                    "Docker on whales will try to download it for you. \n"
                    "Don't worry, it "
                    "won't be in the PATH and won't have anything to do with "
                    "the package manager of your system. \n"
                    "Note: We are not installing the docker daemon, which is a lot "
                    "heavier and harder to install. We're just downloading a single "
                    "standalone binary file.\n"
                    "If you want to trigger the download of the client binary file "
                    "manually (for example if you want to do it in a Dockerfile), "
                    "you can run the following command:\n "
                    "$ python-on-whales download-cli \n"
                )
                download_docker_cli()
                self.client_binary_path = DOCKER_BINARY_PATH
        return self.client_binary_path

    @property
    def docker_cmd(self) -> Command:

        result = Command([self.get_docker_path()])

        if self.config is not None:
            result += ["--config", self.config]

        if self.context is not None:
            result += ["--context", self.context]

        if self.debug:
            result.append("--debug")

        if self.host is not None:
            result += ["--host", self.host]

        if self.log_level is not None:
            result += ["--log-level", self.log_level]

        if self.tls:
            result.append("--tls")

        if self.tlscacert is not None:
            result += ["--tlscacert", self.tlscacert]

        if self.tlscert is not None:
            result += ["--tlscert", self.tlscert]

        if self.tlskey is not None:
            result += ["--tlskey", self.tlskey]

        if self.tlsverify:
            result.append("--tlsverify")

        return result


class DockerCLICaller:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config

    @property
    def docker_cmd(self) -> Command:
        return self.client_config.docker_cmd


class ReloadableObject(DockerCLICaller):
    def __init__(
        self,
        client_config: ClientConfig,
        id_in_inspect: str,
        reference_or_id: str,
        is_immutable_id: bool = False,
    ):
        super().__init__(client_config)
        self._last_refreshed_time = datetime.min
        self._inspect_result = None
        self._immutable_id = None
        self._reference = None
        self._id_in_inspect = id_in_inspect
        if is_immutable_id:
            self._immutable_id = reference_or_id
        else:
            self._set_inspect_result(
                self._fetch_and_parse_inspect_result(reference_or_id)
            )
            self._immutable_id = getattr(self._inspect_result, self._id_in_inspect)

    def __eq__(self, other):
        return (
            self._get_immutable_id() == other._get_immutable_id()
            and self.client_config == other.client_config
        )

    def __str__(self):
        return self._get_immutable_id()

    def _needs_reload(self) -> bool:
        return (datetime.now() - self._last_refreshed_time) >= timedelta(
            seconds=CACHE_VALIDITY_PERIOD
        )

    def reload(self):
        self._set_inspect_result(
            self._fetch_and_parse_inspect_result(self._immutable_id)
        )

    def _fetch_and_parse_inspect_result(self, reference: str):
        raise NotImplementedError

    def _get_inspect_result(self):
        if self._needs_reload():
            self.reload()
        return self._inspect_result

    def _set_inspect_result(self, inspect_result):
        self._inspect_result = inspect_result
        self._last_refreshed_time = datetime.now()

    def _get_immutable_id(self):
        if self._immutable_id is None:
            self.reload()
        return self._immutable_id

    def __hash__(self):
        # maybe we can do better.
        return hash(self._get_immutable_id())


class ReloadableObjectFromJson(ReloadableObject):
    def _fetch_inspect_result_json(self, reference):
        raise NotImplementedError

    def _parse_json_object(self, json_object: Dict[str, Any]):
        raise NotImplementedError

    def _fetch_and_parse_inspect_result(self, reference: str):
        json_str = self._fetch_inspect_result_json(reference)
        json_object = json.loads(json_str)[0]
        return self._parse_json_object(json_object)


def bulk_reload(docker_objects: List[ReloadableObjectFromJson]):
    assert len(set(x.client_config for x in docker_objects)) == 1
    all_ids = [x._get_immutable_id() for x in docker_objects]
    full_cmd = docker_objects[0].docker_cmd + ["inspect"] + all_ids
    json_str = run(full_cmd)
    for json_obj, docker_object in zip(json.loads(json_str), docker_objects):
        docker_object._set_inspect_result(docker_object._parse_json_object(json_obj))
