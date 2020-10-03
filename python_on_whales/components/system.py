from python_on_whales.client_config import DockerCLICaller
from python_on_whales.utils import run


class SystemCLI(DockerCLICaller):
    def disk_free(self):
        """Not yet implemented"""
        raise NotImplementedError

    def events(self):
        """Not yet implemented"""
        raise NotImplementedError

    def info(self):
        """Not yet implemented"""
        raise NotImplementedError

    def prune(self, all: bool = False, volumes: bool = False):
        """Remove unused docker data

        # Arguments
            all: Remove all unused images not just dangling ones
            volumes: Prune volumes
        """
        full_cmd = self.docker_cmd + ["system", "prune"]
        full_cmd.add_flag("--all", all)
        full_cmd.add_flag("--volumes", volumes)
        run(full_cmd)
