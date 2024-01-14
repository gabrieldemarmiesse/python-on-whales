import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Generator, List

import pydantic
import pytest

from python_on_whales import DockerClient

logger = logging.getLogger(__name__)

#
# -----------------------------------------------------------------------------
# Fixtures


def _get_ctr_client(client_type: str, pytestconfig: pytest.Config) -> DockerClient:
    ctr_exe = pytestconfig.getoption(f"--{client_type}-exe")
    client = DockerClient(client_call=[ctr_exe], client_type=client_type)
    try:
        # TODO: Implement 'DockerClient.version' and use that instead.
        subprocess.run(
            [ctr_exe, "version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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
            reason = "\n" + exc.stderr.strip()
        elif isinstance(exc, subprocess.TimeoutExpired):
            reason = f"timed out after {exc.timeout} seconds"
        elif isinstance(exc, FileNotFoundError):
            reason = "executable not found"
        logger.warning(
            "Unable to get %s version with command '%s version': %s",
            client_type,
            ctr_exe,
            reason,
        )
        if pytestconfig.getoption("--no-runtime-skip"):
            pytest.fail(f"{client_type} unavailable")
        else:
            pytest.skip(f"{client_type} unavailable")

    return client


@pytest.fixture(scope="session")
def docker_client(pytestconfig: pytest.Config) -> DockerClient:
    return _get_ctr_client("docker", pytestconfig)


@pytest.fixture(scope="session")
def podman_client(
    pytestconfig: pytest.Config, request: pytest.FixtureRequest
) -> DockerClient:
    return _get_ctr_client("podman", pytestconfig)


# This is function-scoped so that all of a testcase's parameterisations run
# in a row, before running other testcases.
@pytest.fixture(scope="function")
def ctr_client(request: pytest.FixtureRequest) -> DockerClient:
    """Allows to parametrize a test with the container runtime as a string."""
    return request.getfixturevalue(f"{request.param}_client")


@pytest.fixture(scope="function")
def docker_registry(docker_client: DockerClient) -> Generator[str, None, None]:
    yield from _docker_registry(docker_client)


@pytest.fixture(scope="function")
def docker_registry_without_login(
    docker_client: DockerClient,
) -> Generator[str, None, None]:
    yield from _docker_registry(docker_client, login=False)


def _docker_registry(docker_client: DockerClient, login=True) -> str:
    encrypted_password = docker_client.run(
        "mhenry07/apache2-utils",
        ["htpasswd", "-Bbn", "my_user", "my_password"],
        remove=True,
    )
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        htpasswd_file = tmp_path / "htpasswd"
        htpasswd_file.write_text(encrypted_password)
        registry = docker_client.container.create(
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
                docker_client.login(
                    "localhost:5000", username="my_user", password="my_password"
                )
            yield "localhost:5000"


@pytest.fixture(scope="function")
def swarm_mode(docker_client: DockerClient) -> Generator[None, None, None]:
    docker_client.swarm.init()
    yield
    docker_client.swarm.leave(force=True)
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
    pow_group.addoption(
        "--no-runtime-skip",
        action="store_true",
        help="Do not skip tests corresponding to a container runtime that is not available",
    )


def pytest_configure(config: pytest.Config) -> None:
    # Filter warnings
    if not pydantic.__version__.startswith("1"):
        config.addinivalue_line(
            "filterwarnings", "error::pydantic.PydanticDeprecatedSince20"
        )


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: List[pytest.Item]
) -> None:
    # Apply marks to testcases.
    for item in items:
        assert isinstance(item, pytest.Function)
        for runtime in ["docker", "podman"]:
            if f"{runtime}_client" in item.fixturenames:
                item.add_marker(runtime)
            if (
                hasattr(item, "callspec")
                and "ctr_client" in item.callspec.params
                and item.callspec.params["ctr_client"] == runtime
            ):
                item.add_marker(runtime)
