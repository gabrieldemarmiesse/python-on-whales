import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .utils import ValidPath, run


@dataclass(frozen=True)
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
    version: bool = False

    @property
    def docker_cmd(self) -> List[str]:
        result = ["docker"]

        if self.config is not None:
            result += ["--config", self.config]

        return result


class DockerCLICaller:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config

    @property
    def docker_cmd(self) -> List[str]:
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
        if is_immutable_id:
            self._immutable_id = reference_or_id
        else:
            self._reference = reference_or_id
        self._id_in_inspect = id_in_inspect

    def __eq__(self, other):
        return (
            self._get_immutable_id() == other._get_immutable_id()
            and self.client_config == other.client_config
        )

    def __str__(self):
        return self._get_immutable_id()

    def _needs_reload(self) -> bool:
        return (datetime.now() - self._last_refreshed_time) >= timedelta(seconds=0.05)

    def reload(self):
        if self._immutable_id is not None:
            self._set_inspect_result(
                self._fetch_and_parse_inspect_result(self._immutable_id)
            )
        else:
            self._set_inspect_result(
                self._fetch_and_parse_inspect_result(self._reference)
            )
            self._immutable_id = getattr(self._inspect_result, self._id_in_inspect)

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
