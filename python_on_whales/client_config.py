import json
import shutil
import tempfile
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Union

import pydantic

from . import utils
from .utils import ValidPath, run, to_list

CACHE_VALIDITY_PERIOD = 0.01


class ParsingError(Exception):
    pass


class ClientNotFoundError(Exception):
    pass


class Command(list):
    def add_simple_arg(self, name: str, value: Any):
        if value is not None:
            self.extend([name, value])

    def add_flag(self, name: str, value: bool):
        if value:
            self.append(name)

    def add_args_iterable(self, arg_name: str, values: Iterable[Any]):
        for value in values:
            self.extend([arg_name, value])

    def add_args_iterable_or_single(
        self, arg_name: str, iterable_or_single: Union[Iterable[Any], Any]
    ):
        for value in to_list(iterable_or_single):
            self.extend([arg_name, value])

    def add_args_mapping(
        self, arg_name: str, mapping: Mapping[Any, Any], *, separator="="
    ):
        self.add_args_iterable(
            arg_name, utils.format_mapping_for_cli(mapping, separator)
        )

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
    compose_files: List[ValidPath] = field(default_factory=list)
    compose_profiles: List[str] = field(default_factory=list)
    compose_env_file: Optional[ValidPath] = None
    compose_env_files: Iterable[ValidPath] = field(default_factory=list)
    compose_project_name: Optional[str] = None
    compose_project_directory: Optional[ValidPath] = None
    compose_compatibility: Optional[bool] = None
    client_call: List[str] = field(default_factory=lambda: ["docker"])
    client_type: Literal["docker", "podman", "nerdctl", "unknown"] = "unknown"
    _client_call_with_path: Optional[List[Union[Path, str]]] = None

    def get_client_call_with_path(self) -> List[Union[Path, str]]:
        if self._client_call_with_path is None:
            self._client_call_with_path = [
                Path(self._get_docker_path())
            ] + self.client_call[1:]

        return self._client_call_with_path

    def _get_docker_path(self) -> str:
        which_result = shutil.which(self.client_call[0])
        if which_result is None:
            raise ClientNotFoundError(
                f"The binary '{self.client_call[0]}' could not be found on your PATH. "
                "Please ensure that your PATH has the directory of the binary you're looking for. "
                "You can use `print(os.environ['PATH'])` to verify what directories are in your PATH."
            )
        return which_result

    @property
    def docker_cmd(self) -> Command:
        result = Command(self.get_client_call_with_path())

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

    @property
    def docker_compose_cmd(self) -> Command:
        base_cmd = self.docker_cmd + ["compose"]
        base_cmd.add_args_iterable_or_single("--file", self.compose_files)
        base_cmd.add_args_iterable_or_single("--profile", self.compose_profiles)
        if self.compose_env_files:
            if self.compose_env_file:
                warnings.warn(
                    "You can't set both `compose_env_file` and `compose_env_files`. Files used in `compose_env_files` will be used."
                )
            base_cmd.add_args_iterable("--env-file", self.compose_env_files)
        elif self.compose_env_file:
            warnings.warn(
                "`compose_env_file` is deprecated. Use `compose_env_files` instead."
            )
            base_cmd.add_simple_arg("--env-file", self.compose_env_file)

        base_cmd.add_simple_arg("--project-name", self.compose_project_name)
        base_cmd.add_simple_arg("--project-directory", self.compose_project_directory)
        base_cmd.add_flag("--compatibility", self.compose_compatibility)
        return base_cmd


class DockerCLICaller:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config

    @property
    def docker_cmd(self) -> Command:
        return self.client_config.docker_cmd

    @property
    def docker_compose_cmd(self) -> Command:
        return self.client_config.docker_compose_cmd


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
        if not isinstance(other, ReloadableObject):
            return False
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
        json_object = self._fetch_inspect_result_json(reference)
        try:
            return self._parse_json_object(json_object)
        except pydantic.ValidationError as err:
            fd, json_response_file = tempfile.mkstemp(suffix=".json", text=True)
            with open(json_response_file, "w") as f:
                json.dump(json_object, f, indent=2)

            raise ParsingError(
                f"There was an error parsing the json response from the Docker daemon. \n"
                f"This is a bug with python-on-whales itself. Please head to \n"
                f"https://github.com/gabrieldemarmiesse/python-on-whales/issues \n"
                f"and open an issue. You should copy this error message and \n"
                f"the json response from the Docker daemon. The json response was put \n"
                f"in {json_response_file} because it's a bit too big to be printed \n"
                f"on the screen. Make sure that there are no sensitive data in the \n"
                f"json file before copying it in the github issue."
            ) from err


def bulk_reload(docker_objects: List[ReloadableObjectFromJson]):
    assert len(set(x.client_config for x in docker_objects)) == 1
    all_ids = [x._get_immutable_id() for x in docker_objects]
    full_cmd = docker_objects[0].docker_cmd + ["inspect"] + all_ids
    json_str = run(full_cmd)
    for json_obj, docker_object in zip(json.loads(json_str), docker_objects):
        docker_object._set_inspect_result(docker_object._parse_json_object(json_obj))
