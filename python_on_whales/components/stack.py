from typing import List, Optional, Union

import python_on_whales.components.service
from python_on_whales.client_config import DockerCLICaller
from python_on_whales.utils import ValidPath, run, to_list


class Stack:
    def __init__(self, client_config, name):
        self.client_config = client_config
        self.name = name

    def __str__(self):
        return self.name

    def remove(self) -> None:
        StackCLI(self.client_config).remove(self)


ValidStack = Union[str, Stack]


class StackCLI(DockerCLICaller):
    def deploy(
        self,
        name: str,
        compose_files: Union[ValidPath, List[ValidPath]] = [],
        orchestrator: Optional[str] = None,
        prune: bool = False,
        resolve_image: str = "always",
        with_registry_auth: bool = False,
    ) -> Stack:
        full_cmd = self.docker_cmd + ["stack", "deploy"]

        full_cmd.add_args_list("--compose-file", compose_files)
        full_cmd.add_simple_arg("--orchestrator", orchestrator)
        full_cmd.add_flag("--prune", prune)
        full_cmd.add_simple_arg("--resolve-image", resolve_image)
        full_cmd.add_flag("--with-registry-auth", with_registry_auth)
        full_cmd.append(name)
        run(full_cmd, capture_stdout=False, capture_stderr=False)
        return Stack(self.client_config, name)

    def list(self) -> List[Stack]:
        full_cmd = self.docker_cmd + ["stack", "ls", "--format", "{{.Name}}"]
        stacks_names = run(full_cmd).splitlines()
        return [Stack(self.client_config, name) for name in stacks_names]

    def ps(self):
        """Not yet implemented"""
        raise NotImplementedError

    def remove(self, x: Union[ValidStack, List[ValidStack]]) -> None:
        full_cmd = self.docker_cmd + ["stack", "remove"] + to_list(x)
        run(full_cmd)

    def services(
        self, stack: ValidStack
    ) -> List[python_on_whales.components.service.Service]:
        full_cmd = self.docker_cmd + ["stack", "services", "--quiet", stack]
        ids = run(full_cmd).splitlines()
        return [
            python_on_whales.components.service.Service(self.client_config, id_)
            for id_ in ids
        ]
