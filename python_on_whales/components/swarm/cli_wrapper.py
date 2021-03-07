from datetime import timedelta
from typing import Optional, Union

from python_on_whales.client_config import DockerCLICaller
from python_on_whales.utils import ValidPath, run


class SwarmCLI(DockerCLICaller):
    def ca(
        self,
        ca_certificate: ValidPath = None,
        ca_key: ValidPath = None,
        certificate_expiry: Union[int, timedelta] = None,
        detach: bool = False,
        external_ca: str = None,
        rotate: bool = False,
    ):
        """Get and rotate the root CA

        # Arguments
            ca_certificate: Path to the PEM-formatted root CA certificate
                to use for the new cluster
            ca_key: Path to the PEM-formatted root CA key to use
                for the new cluster
            certificate_expiry: Validity period for node certificates
            detach: Exit immediately instead of waiting for the root rotation
                to converge. The function will return `None`.
            external_ca: Specifications of one or more certificate signing endpoints
            rotate: Rotate the swarm CA - if no certificate or key are provided,
                new ones will be generated.
        """
        full_cmd = self.docker_cmd + ["swarm", "ca"]

        full_cmd.add_simple_arg("--ca-cert", ca_certificate)
        full_cmd.add_simple_arg("--ca-key", ca_key)
        full_cmd.add_simple_arg(
            "--cert-expiry", stringify_timedelta_for_docker_cli(certificate_expiry)
        )
        full_cmd.add_flag("--detach", detach)
        full_cmd.add_simple_arg("--external-ca", external_ca)
        full_cmd.add_flag("--rotate", rotate)

        run(full_cmd)
        if not detach:
            # in "docker swarm ca --rotate", the progress is in stdout, not stderr
            # so we need to run the command a second time to be clean.
            return run(self.docker_cmd + ["swarm", "ca"])

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

    def unlock(self, key: str) -> None:
        """Unlock a swarm after the `--autolock` parameter was used and
        the daemon restarted.

        # Arguments:
            key: The key to unlock the swarm. The key can be obtained on any manager
                with `docker.swarm.unlock_key()`.
        """
        full_cmd = self.docker_cmd + ["swarm", "unlock"]
        run(full_cmd, input=key.encode("utf-8"))

    def unlock_key(self, rotate: bool = False) -> str:
        """Gives you the key needed to unlock the swarm after a manager daemon reboot.

        # Arguments
            rotate: Rotate the unlock key.
        """
        full_cmd = self.docker_cmd + ["swarm", "unlock-key", "--quiet"]
        full_cmd.add_flag("--rotate", rotate)
        return run(full_cmd)

    def update(
        self,
        autolock: Optional[bool] = None,
        cert_expiry: Optional[timedelta] = None,
        dispatcher_heartbeat: Optional[timedelta] = None,
        external_ca: Optional[str] = None,
        max_snapshots: Optional[int] = None,
        snapshot_interval: Optional[int] = None,
        task_history_limit: Optional[int] = None,
    ):
        """Update the swarm configuration

        # Arguments
            autolock: Change manager autolocking setting
            cert_expiry: Validity period for node certificates, default
                is `datetime.timedelta(days=90)`. If `int`, it's a number of seconds.
            dispatcher_heartbeat: Dispatcher heartbeat period.
            external_ca: Specifications of one or more certificate signing endpoints
            max_snapshots: Number of additional Raft snapshots to retain
            snapshot_interval: Number of log entries between Raft snapshots (default 10000)
            task_history_limit: Task history retention limit (default 5)
        """
        full_cmd = self.docker_cmd + ["swarm", "update"]
        autolock = format_bool_for_cli(autolock)
        if autolock is not None:
            full_cmd.append(f"--autolock={autolock}")
        full_cmd.add_simple_arg(
            "--cert-expiry", stringify_timedelta_for_docker_cli(cert_expiry)
        )
        full_cmd.add_simple_arg(
            "--dispatcher-heartbeat",
            stringify_timedelta_for_docker_cli(dispatcher_heartbeat),
        )
        full_cmd.add_simple_arg("--external-ci", external_ca)
        full_cmd.add_simple_arg("--max-snapshots", max_snapshots)
        full_cmd.add_simple_arg("--snapshot-interval", snapshot_interval)
        full_cmd.add_simple_arg("--task-history-limit", task_history_limit)
        run(full_cmd)


def format_bool_for_cli(flag: Optional[bool]) -> Optional[str]:
    if flag is None:
        return
    return str(flag).lower()


def stringify_timedelta_for_docker_cli(
    delta: Union[None, int, timedelta]
) -> Optional[str]:
    if delta is None:
        return

    if isinstance(delta, timedelta):
        delta = delta.total_seconds()

    return f"{delta}s"
