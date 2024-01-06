import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, List, Mapping

import pydantic
import pytest

from python_on_whales import DockerClient, docker

logger = logging.getLogger(__name__)


#
# -----------------------------------------------------------------------------
# Fixtures


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


#
# -----------------------------------------------------------------------------
# Pytest hooks


def pytest_addoption(parser: pytest.Parser) -> None:
    """Pytest hook for adding CLI options."""

    # Python-on-whales args
    pow_group = parser.getgroup("python-on-whales")
    pow_group.addoption(
        "--ctr-exe",
        metavar="EXE",
        type=lambda x: x.split(","),
        default=[],
        help=(
            "Comma-separated list of executables to run the tests with, "
            "defaults to using docker, and parameterising with podman if "
            "available"
        ),
    )


def _get_ctr_clients(ctr_exes: List[str]) -> List[DockerClient]:
    ctr_clients: List[DockerClient] = []
    if not ctr_exes:
        # Default to using docker, plus podman if available.
        docker_client = DockerClient()
        docker_client.ctr_mgr = "docker"
        ctr_clients.append(docker_client)
        try:
            subprocess.check_call(
                ["podman", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Unable to parameterise the tests with podman")
        else:
            podman_client = DockerClient(client_call=["podman"])
            podman_client.ctr_mgr = "podman"
            ctr_clients.append(podman_client)
    else:
        unsupported_ctr_exes: List[str] = []
        for exe in ctr_exes:
            client = DockerClient(client_call=[exe])
            # Check the client is available by running '<client> --version'.
            try:
                version_output = subprocess.check_output([exe, "--version"], text=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                unsupported_ctr_exes.append(exe)
                continue
            # Check the daemon is running (if required) with '<client> version'.
            try:
                subprocess.check_call([exe, "version"], stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                unsupported_ctr_exes.append(exe)
                continue

            ctr_clients.append(client)

            # Deduce whether docker or podman from version output.
            if "docker" in version_output.lower():
                client.ctr_mgr = "docker"
            elif "podman" in version_output.lower():
                client.ctr_mgr = "podman"
            else:
                logger.warning(
                    f"Unrecognised container manager from '{exe} --version', "
                    "assuming docker"
                )
                client.ctr_mgr = "docker"

        if unsupported_ctr_exes:
            raise Exception(
                "'<ctr_exe> --version' failed for the following specified exes: "
                + ",".join(unsupported_ctr_exes)
            )

    return ctr_clients


def pytest_configure(config: pytest.Config) -> None:
    # Filter warnings
    if not pydantic.__version__.startswith("1"):
        config.addinivalue_line(
            "filterwarnings", "error::pydantic.PydanticDeprecatedSince20"
        )
    # Register markers
    config.addinivalue_line(
        "markers",
        "ctr_mgr(MGR, MGR, ...): Container managers supported by the test",
    )
    # Determine supported container managers.
    config.ctr_clients = _get_ctr_clients(config.getoption("--ctr-exe"))


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "ctr_client" in metafunc.fixturenames:
        metafunc.parametrize(
            "ctr_client",
            metafunc.config.ctr_clients,
            ids=[
                client.client_config.client_call[0]
                for client in metafunc.config.ctr_clients
            ],
        )


def pytest_collection_modifyitems(
    config: pytest.Config, items: List[pytest.Item]
) -> None:
    # Find paramaterisations that don't make sense and remove them from
    # the list of tests to be run.
    remove_tests = []
    for item in items:
        assert isinstance(item, pytest.Function)
        if not hasattr(item, "callspec"):
            continue
        test_params: Mapping[str, Any] = item.callspec.params
        if "ctr_client" in test_params and (
            marker := item.get_closest_marker("ctr_mgr")
        ):
            if test_params["ctr_client"].ctr_mgr not in marker.args[0]:
                remove_tests.append(item)
    logger.debug("Removing %d parameterised tests", len(remove_tests))
    items[:] = [x for x in items if x not in remove_tests]
