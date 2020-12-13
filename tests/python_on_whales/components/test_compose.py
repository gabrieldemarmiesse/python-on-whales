import os

import pytest

from python_on_whales import DockerClient

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_COMPOSE_TESTS", "0") == "0", reason="Do not run compose tests"
)

docker = DockerClient(compose_files=["./dummy_compose.yml"])


def test_docker_compose_build():
    docker.compose.build()
    docker.compose.build(["my_service"])


def test_docker_compose_up_down():
    docker.compose.up(detach=True)
    docker.compose.down()


def test_docker_compose_up_down_some_services():
    docker.compose.up(["my_service", "redis"], detach=True)
    docker.compose.down()
