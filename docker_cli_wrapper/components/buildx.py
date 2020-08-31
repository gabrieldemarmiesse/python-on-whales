from typing import Dict, List, Optional

from typeguard import typechecked

from docker_cli_wrapper.utils import ValidPath, run


class BuildxCLI:
    def __init__(self, docker_cmd: List[str]):
        self.docker_cmd = docker_cmd

    def _make_cli_cmd(self) -> List[str]:
        return self.docker_cmd + ["buildx"]

    @typechecked
    def build(
        self,
        context_path: ValidPath,
        add_hosts: List[str] = [],
        allow: List[str] = [],
        build_args: List[str] = [],
        cache_from=None,
        cache_to=None,
        file: Optional[ValidPath] = None,
        iidfile=None,
        labels: List[Dict[str, str]] = [],
        load: Optional[bool] = None,
        network: Optional[str] = None,
        cache: bool = True,
        output=None,
        platform: Optional[str] = None,
        progress: str = "auto",
        pull: bool = False,
        push: bool = False,
        secrets: List[Dict[str, str]] = [],
        ssh: Optional[str] = None,
        tags: List[str] = [],
        target: Optional[str] = None,
    ):

        full_cmd = self._make_cli_cmd() + ["build"]

        if progress != "auto":
            full_cmd += ["--progress", progress]

        if pull:
            full_cmd.append("--pull")
        if push:
            full_cmd.append("--push")

        if file is not None:
            full_cmd += ["--file", str(file)]

        if target is not None:
            full_cmd += ["--target", target]

        full_cmd.append(str(context_path))

        dood = run(full_cmd, capture_stderr=False)
