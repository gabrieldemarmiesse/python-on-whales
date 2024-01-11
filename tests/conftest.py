import subprocess
import tempfile
import time
from pathlib import Path
from typing import Generator, Tuple, Union

import pydantic
import pytest
from typing_extensions import Literal

from python_on_whales import DockerClient
from python_on_whales.test_utils import DOCKER_TEST_FLAG, PODMAN_TEST_FLAG

#
# -----------------------------------------------------------------------------
# Fixtures


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
            stderr=subprocess.PIPE,
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
            reason = "\n" + exc.stderr
        elif isinstance(exc, subprocess.TimeoutExpired):
            reason = f"timed out after {exc.timeout} seconds"
        elif isinstance(exc, FileNotFoundError):
            reason = "executable not found"
        command = " ".join(ctr_client.client_config.client_call)
        return False, (
            f"Unable to get version with command '{command} version': {reason}"
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
def docker_client(pytestconfig):
    client = DockerClient(
        client_call=[pytestconfig.getoption("--docker-exe")], client_type="docker"
    )
    yield TestSessionClient(client)


@pytest.fixture(scope="session")
def podman_client(pytestconfig):
    client = DockerClient(
        client_call=[pytestconfig.getoption("--podman-exe")], client_type="podman"
    )
    yield TestSessionClient(client)


@pytest.fixture
def ctr_client(
    request: pytest.FixtureRequest,
    docker_client: TestSessionClient,
    podman_client: TestSessionClient,
) -> Generator[DockerClient, None, None]:
    """Allows to parametrize a test with the container runtime as a string."""
    if request.param == DOCKER_TEST_FLAG:
        request.applymarker(pytest.mark.docker)
        yield docker_client.get_ctr_client()
    elif request.param == PODMAN_TEST_FLAG:
        request.applymarker(pytest.mark.podman)
        yield podman_client.get_ctr_client()
    else:
        raise ValueError(f"Unknown container runtime {request.param}")


@pytest.fixture(scope="function")
def docker_registry(ctr_client: DockerClient) -> Generator[str, None, None]:
    yield from _docker_registry(ctr_client)


@pytest.fixture(scope="function")
def docker_registry_without_login(
    ctr_client: DockerClient,
) -> Generator[str, None, None]:
    yield from _docker_registry(ctr_client, login=False)


def _docker_registry(ctr_client: DockerClient, login=True) -> str:
    encrypted_password = ctr_client.run(
        "mhenry07/apache2-utils",
        ["htpasswd", "-Bbn", "my_user", "my_password"],
        remove=True,
    )
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        htpasswd_file = tmp_path / "htpasswd"
        htpasswd_file.write_text(encrypted_password)
        registry = ctr_client.container.create(
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
                ctr_client.login(
                    "localhost:5000", username="my_user", password="my_password"
                )
            yield "localhost:5000"


@pytest.fixture(scope="function")
def swarm_mode(ctr_client: DockerClient) -> Generator[None, None, None]:
    ctr_client.swarm.init()
    yield
    ctr_client.swarm.leave(force=True)
    time.sleep(1)


#
# -----------------------------------------------------------------------------
# Pytest hooks


def pytest_addoption(parser: pytest.Parser) -> None:
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


def pytest_configure(config: pytest.Config) -> None:
    # Filter warnings
    if not pydantic.__version__.startswith("1"):
        config.addinivalue_line(
            "filterwarnings", "error::pydantic.PydanticDeprecatedSince20"
        )
