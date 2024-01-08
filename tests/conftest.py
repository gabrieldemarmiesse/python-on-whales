import subprocess
import tempfile
import time
from pathlib import Path
from typing import Tuple, Union

import pydantic
import pytest
from typing_extensions import Literal

from python_on_whales import DockerClient, docker
from python_on_whales.test_utils import DOCKER_TEST_FLAG, PODMAN_TEST_FLAG


def pytest_addoption(parser):
    """Pytest hook for adding CLI options."""

    pow_group = parser.getgroup("python-on-whales")
    for name in ("docker", "podman"):
        pow_group.addoption(
            f"--{name}-exe",
            metavar="EXE",
            default=name,
            help=f"Path to the {name} executable to use in the unit tests."
            f"Defaults to {name}.",
        )


@pytest.fixture
def docker_registry():
    yield from _docker_registry()


@pytest.fixture
def docker_registry_without_login():
    yield from _docker_registry(login=False)


def _docker_registry(login=True):
    encrypted_password = docker.run(
        "mhenry07/apache2-utils",
        ["htpasswd", "-Bbn", "my_user", "my_password"],
        remove=True,
    )
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        htpasswd_file = tmp_path / "htpasswd"
        htpasswd_file.write_text(encrypted_password)
        registry = docker.container.create(
            "registry:2",
            remove=True,
            envs=dict(
                REGISTRY_AUTH="htpasswd",
                REGISTRY_AUTH_HTPASSWD_REALM="Registry Realm",
                REGISTRY_AUTH_HTPASSWD_PATH="/tmp/htpasswd",
            ),
            publish=[(5000, 5000)],
        )
        with registry:
            registry.copy_to(htpasswd_file, "/tmp/htpasswd")
            registry.start()
            time.sleep(1.5)
            if login:
                docker.login(
                    "localhost:5000", username="my_user", password="my_password"
                )
            yield "localhost:5000"


@pytest.fixture
def swarm_mode():
    docker.swarm.init()
    yield
    docker.swarm.leave(force=True)
    time.sleep(1)


def pytest_collection_modifyitems(config, items):
    if pydantic.__version__.startswith("1"):
        return
    for item in items:
        item.add_marker(
            pytest.mark.filterwarnings("error::pydantic.PydanticDeprecatedSince20")
        )


def is_available(
    ctr_client: DockerClient,
) -> Union[Tuple[Literal[True], None], Tuple[Literal[False], str]]:
    """Returns a tuple (True, None) if the container runtime is available
    and (False, reason (str)) if it's not available."""

    try:
        # TODO: Implement 'DockerClient.version' and use that instead.
        subprocess.run(
            ctr_client.client_config.client_call + ["version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
            timeout=10,
        )
        return True, None
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            reason = "\n" + exc.output
        elif isinstance(exc, subprocess.TimeoutExpired):
            reason = f"timed out after {exc.timeout} seconds"
        elif isinstance(exc, FileNotFoundError):
            reason = "executable not found"
        command = " ".join(ctr_client.client_config.client_call)
        return False, (
            f"Unable to get version with command"
            f" '{command} version'. Reason: {reason}"
        )


class TestSessionClient:
    def __init__(self, ctr_client: DockerClient):
        self._ctr_client = ctr_client
        self._available, self._reason = is_available(ctr_client)

    def get_ctr_client(self) -> DockerClient:
        """Try to get the ctr client and skip the entire test if it's not available."""
        if not self._available:
            pytest.skip(self._reason)
        return self._ctr_client


@pytest.fixture(scope="session")
def docker_client_fixture(pytestconfig):
    client = DockerClient(client_call=[pytestconfig.getoption("--docker-exe")])
    yield TestSessionClient(client)


@pytest.fixture(scope="session")
def podman_client_fixture(pytestconfig):
    client = DockerClient(client_call=[pytestconfig.getoption("--podman-exe")])
    yield TestSessionClient(client)


@pytest.fixture
def ctr_client(
    request,
    docker_client_fixture: TestSessionClient,
    podman_client_fixture: TestSessionClient,
):
    """Allows to parametrize a test with the container runtime as a string."""
    if request.param == DOCKER_TEST_FLAG:
        request.applymarker(pytest.mark.docker)
        yield docker_client_fixture.get_ctr_client()
    elif request.param == PODMAN_TEST_FLAG:
        request.applymarker(pytest.mark.podman)
        yield podman_client_fixture.get_ctr_client()
    else:
        raise ValueError(f"Unknown container runtime {request.param}")
