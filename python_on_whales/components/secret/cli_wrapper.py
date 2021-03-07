from typing import Any, Dict, List, Optional, Union

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.secret.models import SecretInspectResult
from python_on_whales.utils import ValidPath, format_dict_for_cli, run, to_list


class Secret(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove()

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["secret", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> SecretInspectResult:
        return SecretInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> SecretInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    def remove(self):
        """Remove this Docker secret.

        See the [`docker.secret.remove`](../sub-commands/secret.md#remove) command for
        information about the arguments.
        """
        SecretCLI(self.client_config).remove(self)


ValidSecret = Union[Secret, str]


class SecretCLI(DockerCLICaller):
    def create(
        self,
        name: str,
        file: ValidPath,
        driver: Optional[str] = None,
        labels: Dict[str, str] = {},
        template_driver: Optional[str] = None,
    ) -> Secret:
        """Creates a `python_on_whales.Secret`.

        # Returns
            A `python_on_whales.Secret` object.
        """
        full_cmd = self.docker_cmd + ["secret", "create"]
        full_cmd.add_simple_arg("--driver", driver)
        full_cmd.add_args_list("--label", format_dict_for_cli(labels))
        full_cmd.add_simple_arg("--template-driver", template_driver)
        full_cmd += [name, file]
        return Secret(self.client_config, run(full_cmd), is_immutable_id=True)

    def inspect(self, x: Union[str, List[str]]) -> Union[Secret, List[Secret]]:
        """Returns one or more `python_on_whales.Secret` based on an ID or name.

        # Arguments
            x: One or more IDs/names.
        """
        if isinstance(x, list):
            return [Secret(self.client_config, reference) for reference in x]
        else:
            return Secret(self.client_config, x)

    def list(self, filters: Dict[str, str] = {}) -> List[Secret]:
        """Returns all secrets as a `List[python_on_whales.Secret]`."""
        full_cmd = self.docker_cmd + ["secret", "list", "--quiet"]
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))
        ids = run(full_cmd).splitlines()
        return [Secret(self.client_config, id_, is_immutable_id=True) for id_ in ids]

    def remove(self, x: Union[ValidSecret, List[ValidSecret]]) -> None:
        """Removes one or more secrets

        # Arguments
            x: One or more secrets.
                Name, ids or `python_on_whales.Secret` objects are valid inputs.
        """
        full_cmd = self.docker_cmd + ["secret", "remove"] + to_list(x)
        run(full_cmd)
