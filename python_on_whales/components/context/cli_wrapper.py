from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, overload

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.context.models import (
    ContextEndpoint,
    ContextInspectResult,
    ContextStorage,
)
from python_on_whales.utils import run, to_list


class Context(ReloadableObjectFromJson):
    def __init__(
        self,
        client_config: ClientConfig,
        reference: Optional[str],
        is_immutable_id=False,
    ):
        super().__init__(client_config, "name", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove(force=True)

    def _fetch_inspect_result_json(self, reference: Optional[str]):
        full_cmd = self.docker_cmd + ["context", "inspect"]
        if reference is not None:
            full_cmd.append(reference)
        return run(full_cmd)

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return ContextInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> ContextInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def name(self) -> str:
        return self._get_immutable_id()

    @property
    def metadata(self) -> Dict[str, str]:
        return self._get_inspect_result().metadata

    @property
    def endpoints(self) -> Dict[str, ContextEndpoint]:
        return self._get_inspect_result().endpoints

    @property
    def tls_material(self) -> dict:
        return self._get_inspect_result().tls_material

    @property
    def storage(self) -> ContextStorage:
        return self._get_inspect_result().storage

    def remove(self, force: bool = False) -> None:
        """Removes this context"""
        ContextCLI(self.client_config).remove(self, force)

    def update(self) -> None:
        """Update this context, not yet implemented."""
        raise NotImplementedError
        ContextCLI(self.client_config).update(self)

    def use(self) -> None:
        """Use this context"""
        ContextCLI(self.client_config).use(self)


ValidContext = Union[Context, str]


class ContextCLI(DockerCLICaller):
    def create(self):
        """Not yet implemented"""
        raise NotImplementedError

    @overload
    def inspect(self, x: Union[None, str]) -> Context:
        ...

    @overload
    def inspect(self, x: List[str]) -> List[Context]:
        ...

    def inspect(
        self, x: Union[None, str, List[str]] = None
    ) -> Union[Context, List[Context]]:
        """Returns the context object. If no argument is provided, returns the
        current context."""
        if isinstance(x, str) or x is None:
            return Context(self.client_config, x)
        else:
            return [Context(self.client_config, ref) for ref in x]

    def list(self) -> List[Context]:
        """List all Docker contexts available

        # Returns
            `List[python_on_whales.Context]`
        """

        full_cmd = self.docker_cmd + ["context", "list", "--quiet"]

        ids = run(full_cmd).splitlines()
        return [Context(self.client_config, id_, is_immutable_id=True) for id_ in ids]

    def remove(self, x: Union[ValidContext, List[ValidContext]], force: bool = False):
        """Removes one or more contexts

        # Arguments
            x: One or more contexts
            force: Force the removal of this context
        """
        full_cmd = self.docker_cmd + ["context", "remove"]
        full_cmd.add_flag("--force", force)
        full_cmd += to_list(x)
        run(full_cmd)

    def update(self):
        """Not yet implemented"""
        raise NotImplementedError

    def use(self, context: ValidContext):
        """Set the default context

        # Arguments
            context: The context to set as default
        """
        full_cmd = self.docker_cmd + ["context", "use", context]
        run(full_cmd)
