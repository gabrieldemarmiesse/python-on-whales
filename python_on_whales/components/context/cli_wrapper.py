from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
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
        json_str = run(full_cmd)
        return json.loads(json_str)[0]

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return ContextInspectResult(**json_object)

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

    def __repr__(self):
        return (
            f"python_on_whales.Context(name='{self.name}', endpoints={self.endpoints})"
        )


ValidContext = Union[Context, str]


@dataclass
class DockerContextConfig:
    from_: Optional[ValidContext] = None
    host: Optional[str] = None
    certificate_authority: Union[Path, str, None] = None
    certificate: Union[Path, str, None] = None
    key: Union[Path, str, None] = None
    skip_tls_verify: bool = False

    def format_for_docker_cli(self) -> str:
        list_of_args = []
        if self.from_ is not None:
            list_of_args.append(f"from={self.from_}")
        if self.host is not None:
            list_of_args.append(f"host={self.host}")
        if self.certificate_authority is not None:
            list_of_args.append(f"ca={self.certificate_authority}")
        if self.certificate is not None:
            list_of_args.append(f"cert={self.certificate}")
        if self.key is not None:
            list_of_args.append(f"key={self.key}")
        list_of_args.append(f"skip-tls-verify={self.skip_tls_verify}")

        return ",".join(list_of_args)


@dataclass
class KubernetesContextConfig:
    from_: Optional[ValidContext] = None
    config_file: Union[str, Path, None] = None
    context_override: Optional[str] = None
    namespace_override: Optional[str] = None

    def format_for_docker_cli(self) -> str:
        list_of_args = []
        if self.from_ is not None:
            list_of_args.append(f"from={self.from_}")
        if self.config_file is not None:
            list_of_args.append(f"config-file={self.config_file}")
        if self.context_override is not None:
            list_of_args.append(f"context-override={self.context_override}")
        if self.namespace_override is not None:
            list_of_args.append(f"namespace-override={self.namespace_override}")
        return ",".join(list_of_args)


class ContextCLI(DockerCLICaller):
    def create(
        self,
        context_name: str,
        default_stack_orchestrator: Optional[str] = None,
        description: Optional[str] = None,
        from_: Optional[ValidContext] = None,
        docker: Union[Dict[str, Any], DockerContextConfig, None] = None,
        kubernetes: Union[Dict[str, Any], KubernetesContextConfig, None] = None,
    ) -> Context:
        """Creates a new context

        Parameters:
            context_name: name of the context to create
            default_stack_orchestrator: Default orchestrator for stack operations to use with this context (swarm|kubernetes|all)
            description: Description of the context
            docker: Set the docker endpoint, you can use a dict of a class to
                specify the options. The class is `python_on_whales.DockerContextConfig`.
            from_: Create context from a named context
            kubernetes: Set the kubernetes endpoint. You can use a dict or a class to specify the options. The class
                is `python_on_whales.KubernetesContextConfig`.
        """
        if isinstance(docker, dict):
            docker = DockerContextConfig(**docker)
        if isinstance(kubernetes, dict):
            kubernetes = KubernetesContextConfig(**kubernetes)

        full_cmd = self.docker_cmd + ["context", "create"]

        full_cmd.add_simple_arg(
            "--default-stack-orchestrator", default_stack_orchestrator
        )
        full_cmd.add_simple_arg("--description", description)
        full_cmd.add_simple_arg("--from", from_)
        if docker is not None:
            full_cmd.add_simple_arg("--docker", docker.format_for_docker_cli())
        if kubernetes is not None:
            full_cmd.add_simple_arg("--kubernetes", kubernetes.format_for_docker_cli())
        full_cmd.append(context_name)
        run(full_cmd)
        return self.inspect(context_name)

    @overload
    def inspect(self, x: Union[None, str]) -> Context: ...

    @overload
    def inspect(self, x: List[str]) -> List[Context]: ...

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

        Parameters:
            x: One or more contexts, empty list means no-op.
            force: Force the removal of this context
        """
        full_cmd = self.docker_cmd + ["context", "remove"]
        full_cmd.add_flag("--force", force)
        if x == []:
            return
        full_cmd += to_list(x)
        run(full_cmd)

    def update(self):
        """Not yet implemented"""
        raise NotImplementedError

    def use(self, context: ValidContext):
        """Set the default context

        Parameters:
            context: The context to set as default
        """
        full_cmd = self.docker_cmd + ["context", "use", context]
        run(full_cmd)
        return self.inspect(context)
