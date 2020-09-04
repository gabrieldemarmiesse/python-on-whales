import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

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
        is_id: bool = False,
    ):
        super().__init__(client_config)
        self._last_refreshed_time = datetime.min
        self._inspect_result = None
        self._id = None
        self._reference = None
        if is_id:
            self._id = reference_or_id
        else:
            self._reference = reference_or_id
        self._id_in_inspect = id_in_inspect

    def _needs_reload(self) -> bool:
        return (datetime.now() - self._last_refreshed_time) >= timedelta(seconds=0.2)

    def reload(self):
        if self._id is not None:
            self._set_inspect_result(self.stuff(self._id))
        else:
            self._set_inspect_result(self.stuff(self._reference))
            self._id = getattr(self._inspect_result, self._id_in_inspect)

    def stuff(self, reference: str):
        # to implement
        json_str = run(self.docker_cmd + ["container", "inspect", reference])
        json_obj = json.loads(json_str)[0]
        return xxxxxx.parse_obj(json_obj)

    def _get_inspect_result(self):
        if self._needs_reload():
            self.reload()
        return self._inspect_result

    def _set_inspect_result(self, inspect_result):
        self._inspect_result = inspect_result
        self._last_refreshed_time = datetime.now()
