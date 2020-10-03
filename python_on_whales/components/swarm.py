from typing import Optional

from python_on_whales.client_config import DockerCLICaller
from python_on_whales.utils import run


class SwarmCLI(DockerCLICaller):
    def ca(self):
        """Not yet implemented"""
        raise NotImplementedError

    def init(
        self,
        advertise_address: Optional[str] = None,
        autolock: bool = False,
        availability: str = "active",
        data_path_address: Optional[str] = None,
        data_path_port: Optional[int] = None,
        listen_address: Optional[str] = None,
    ) -> None:
        """Initialize a Swarm.

        If you need the token to join the new swarm from another node,
        use the [`docker.swarm.join_token`](#join_token) function.

        A example of how to initialize the whole swarm without leaving the manager
        if the manager has ssh access to the workers:
        ```python
        from python_on_whales import docker, DockerClient

        worker_docker = DockerClient(host="ssh://worker_linux_user@worker_hostname")
        # Here the docker variable is connected to the local daemon
        # worker_docker is a connected to the Docker daemon of the
        # worker through ssh, useful to control it without login to the machine
        # manually.
        docker.swarm.init()
        my_token = docker.swarm.join_token("worker")  # you can set manager too
        worker_docker.swarm.join("manager_hostname:2377", token=my_token)
        ```

        # Arguments
            advertise_address: Advertised address (format: `<ip|interface>[:port]`)
            autolock: Enable manager autolocking (requiring an unlock key to start a
                stopped manager)
            availability: Availability of the node ("active"|"pause"|"drain")
            data_path_address: Address or interface to use for data path
                traffic (format is `<ip|interface>`)
        """
        full_cmd = self.docker_cmd + ["swarm", "init"]
        full_cmd.add_simple_arg("--advertise-addr", advertise_address)
        full_cmd.add_flag("--autolock", autolock)
        full_cmd.add_simple_arg("--availability", availability)
        full_cmd.add_simple_arg("--data-path-addr", data_path_address)
        full_cmd.add_simple_arg("--data-path-port", data_path_port)
        full_cmd.add_simple_arg("--listen-addr", listen_address)
        run(full_cmd)

    def join(
        self,
        manager_address: str,
        advertise_address: str = None,
        availability: str = "active",
        data_path_address: str = None,
        listen_address: str = None,
        token: str = None,
    ):
        """Joins a swarm

        # Arguments
            manager_address: The address of the swarm manager in the format `"{ip}:{port}"`
            advertise_address: Advertised address (format: <ip|interface>[:port])
            availability: Availability of the node
                (`"active"`|`"pause"`|`"drain"`)
            data_path_address: Address or interface to use for data
                path traffic (format: <ip|interface>)
            listen-address: Listen address (format: <ip|interface>[:port])
                (default 0.0.0.0:2377)
            token: Token for entry into the swarm, will determine if
                the node enters the swarm as a manager or a worker.
        """
        full_cmd = self.docker_cmd + ["swarm", "join"]
        full_cmd.add_simple_arg("--advertise-addr", advertise_address)
        full_cmd.add_simple_arg("--availability", availability)
        full_cmd.add_simple_arg("--data-path-addr", data_path_address)
        full_cmd.add_simple_arg("--listen-addr", listen_address)
        full_cmd.add_simple_arg("--token", token)
        full_cmd.append(manager_address)
        run(full_cmd)

    def join_token(self, node_type: str, rotate: bool = False) -> str:
        """Obtains a token to join the swarm

        This token can then be used
        with `docker.swarm.join("manager:2377", token=my_token)`.

        # Arguments
            node_type: `"manager"` or `"worker"`
            rotate: Rotate join token
        """
        full_cmd = self.docker_cmd + ["swarm", "join-token", "--quiet"]
        full_cmd.add_flag("--rotate", rotate)
        full_cmd.append(node_type)
        return run(full_cmd)

    def leave(self, force: bool = False) -> None:
        """Leave the swarm

        # Arguments
            force: Force this node to leave the swarm, ignoring warnings
        """
        full_cmd = self.docker_cmd + ["swarm", "leave"]
        full_cmd.add_flag("--force", force)
        run(full_cmd)

    def unlock(self):
        """Not yet implemented"""
        raise NotImplementedError

    def unlock_key(self):
        """Not yet implemented"""
        raise NotImplementedError

    def update(self):
        """Not yet implemented"""
        raise NotImplementedError
