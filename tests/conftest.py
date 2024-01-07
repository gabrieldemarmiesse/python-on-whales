import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Generator

import pydantic
import pytest

from python_on_whales import DockerClient

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def ctr_client(pytestconfig: pytest.Config) -> DockerClient:
    ctr_exe = pytestconfig.getoption("--ctr-exe")
    logger.info("Running tests with container exe: %s", ctr_exe)
    client = DockerClient(client_call=[ctr_exe])
    # Check the client is available.
    try:
        # TODO: Implement 'DockerClient.version' and use that instead.
        subprocess.run(
            [ctr_exe, "version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
            timeout=10,
        )
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
        raise RuntimeError(
            f"Unable to run with container exe {ctr_exe!r}.\n"
            f"'{ctr_exe} version' command failed: {reason}"
        ) from exc
    return client


@pytest.fixture(scope="function")
def docker_registry(ctr_client: DockerClient):
    yield from _docker_registry(ctr_client)


@pytest.fixture(scope="function")
def docker_registry_without_login(ctr_client: DockerClient):
    yield from _docker_registry(ctr_client, login=False)


def _docker_registry(ctr_client: DockerClient, login=True):
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


def pytest_addoption(parser: pytest.Parser) -> None:
    """Pytest hook for adding CLI options."""
    pow_group = parser.getgroup("python-on-whales")
    pow_group.addoption(
        "--ctr-exe",
        metavar="EXE",
        default="docker",
        help="Container executable to run the tests with, defaults to using docker",
    )


def pytest_configure(config: pytest.Config) -> None:
    # Filter warnings
    if not pydantic.__version__.startswith("1"):
        config.addinivalue_line(
            "filterwarnings", "error::pydantic.PydanticDeprecatedSince20"
        )
