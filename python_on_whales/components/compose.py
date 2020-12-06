from __future__ import annotations

from typing import Dict, List, Optional, Union

from python_on_whales.client_config import DockerCLICaller


class ComposeCLI(DockerCLICaller):
    def build(
        self,
        services: List[str] = [],
        build_args: Dict[str, str] = {},
        compress: bool = False,
        force_remove: bool = False,
        memory: Union[int, str, None] = None,
        no_cache: bool = False,
        no_remove: bool = False,
        parallel: bool = False,
        progress: Optional[str] = None,
        pull: bool = False,
        quiet: bool = False,
    ):
        """Not yet implemented"""
        raise NotImplementedError

    def config(self):
        """Not yet implemented"""
        raise NotImplementedError

    def create(self):
        """Not yet implemented"""
        raise NotImplementedError

    def down(self):
        """Not yet implemented"""
        raise NotImplementedError

    def events(self):
        """Not yet implemented"""
        raise NotImplementedError

    def exec(self):
        """Not yet implemented"""
        raise NotImplementedError

    def images(self):
        """Not yet implemented"""
        raise NotImplementedError

    def kill(self):
        """Not yet implemented"""
        raise NotImplementedError

    def logs(self):
        """Not yet implemented"""
        raise NotImplementedError

    def pause(self):
        """Not yet implemented"""
        raise NotImplementedError

    def port(self):
        """Not yet implemented"""
        raise NotImplementedError

    def ps(self):
        """Not yet implemented"""
        raise NotImplementedError

    def pull(self):
        """Not yet implemented"""
        raise NotImplementedError

    def push(self):
        """Not yet implemented"""
        raise NotImplementedError

    def restart(self):
        """Not yet implemented"""
        raise NotImplementedError

    def rm(self):
        """Not yet implemented"""
        raise NotImplementedError

    def run(self):
        """Not yet implemented"""
        raise NotImplementedError

    def scale(self):
        """Not yet implemented"""
        raise NotImplementedError

    def start(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stop(self):
        """Not yet implemented"""
        raise NotImplementedError

    def top(self):
        """Not yet implemented"""
        raise NotImplementedError

    def unpause(self):
        """Not yet implemented"""
        raise NotImplementedError

    def up(self):
        """Not yet implemented"""
        raise NotImplementedError

    def version(self):
        """Not yet implemented"""
        raise NotImplementedError
