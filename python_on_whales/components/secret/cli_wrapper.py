import datetime as dt
import json
import warnings
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Union,
)

from typing_extensions import TypeAlias

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.secret.models import SecretInspectResult, SecretSpec
from python_on_whales.utils import ValidPath, format_mapping_for_cli, run, to_list

SecretListFilter: TypeAlias = Union[
    Tuple[Literal["id"], str],
    Tuple[Literal["label"], str],
    Tuple[Literal["name"], str],
]


class Secret(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        print("reference: ", reference)
        super().__init__(client_config, "id", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove()

    def _fetch_inspect_result_json(self, reference):
        json_str = run(self.docker_cmd + ["secret", "inspect", reference])
        return json.loads(json_str)[0]

    def _parse_json_object(self, json_object: Dict[str, Any]) -> SecretInspectResult:
        return SecretInspectResult(**json_object)

    def _get_inspect_result(self) -> SecretInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def created_at(self) -> dt.datetime:
        return self._get_inspect_result().created_at

    @property
    def updated_at(self) -> dt.datetime:
        return self._get_inspect_result().updated_at

    @property
    def spec(self) -> SecretSpec:
        return self._get_inspect_result().spec

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
        full_cmd.add_args_iterable_or_single("--label", format_mapping_for_cli(labels))
        full_cmd.add_simple_arg("--template-driver", template_driver)
        full_cmd += [name, file]
        return Secret(self.client_config, run(full_cmd), is_immutable_id=True)

    def inspect(self, x: Union[str, List[str]]) -> Union[Secret, List[Secret]]:
        """Returns one or more `python_on_whales.Secret` based on an ID or name.

        Parameters:
            x: One or more IDs/names.
        """
        if isinstance(x, list):
            return [Secret(self.client_config, reference) for reference in x]
        else:
            return Secret(self.client_config, x)

    def list(
        self, filters: Union[Iterable[SecretListFilter], Mapping[str, Any]] = ()
    ) -> List[Secret]:
        """Returns all secrets as a `List[python_on_whales.Secret]`."""
        if isinstance(filters, Mapping):
            filters = filters.items()
            warnings.warn(
                "Passing filters as a mapping is deprecated, replace with an "
                "iterable of tuples instead, as so:\n"
                f"filters={list(filters)}",
                DeprecationWarning,
            )
        full_cmd = self.docker_cmd + ["secret", "list", "--quiet"]
        full_cmd.add_args_iterable("--filter", (f"{f[0]}={f[1]}" for f in filters))
        ids = run(full_cmd).splitlines()
        return [Secret(self.client_config, id_, is_immutable_id=True) for id_ in ids]

    def remove(self, x: Union[ValidSecret, List[ValidSecret]]) -> None:
        """Removes one or more secrets

        Parameters:
            x: One or more secrets.
                Name, ids or `python_on_whales.Secret` objects are valid inputs.
        """
        if x == []:
            return
        full_cmd = self.docker_cmd + ["secret", "remove"] + to_list(x)
        run(full_cmd)
