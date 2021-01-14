from python_on_whales import DockerClient
from python_on_whales.utils import PROJECT_ROOT

docker = DockerClient(
    compose_files=[PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"]
)


def test_docker_compose_build():
    docker.compose.build()
    docker.compose.build(["my_service"])


def test_docker_compose_up_down():
    docker.compose.up(detach=True)
    docker.compose.down()


def test_docker_compose_up_down_some_services():
    docker.compose.up(["my_service", "redis"], detach=True)
    docker.compose.down()
