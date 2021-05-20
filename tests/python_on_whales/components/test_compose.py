from datetime import timedelta

import pytest

import python_on_whales
from python_on_whales import DockerClient, DockerException
from python_on_whales.utils import PROJECT_ROOT

pytestmark = pytest.mark.skipif(
    not python_on_whales.docker.compose.is_installed(),
    reason="Those tests need docker compose.",
)

docker = DockerClient(
    compose_files=[PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"]
)


def test_docker_compose_build():
    docker.compose.build()
    docker.compose.build(["my_service"])
    docker.image.remove("some_random_image")


def test_docker_compose_up_down():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_ends_quickly.yml"
        ]
    )
    docker.compose.up(["busybox", "alpine"])


def test_no_containers():
    assert docker.compose.ps() == []


def test_docker_compose_up_detach_down():
    docker.compose.up(detach=True)
    docker.compose.down()


def test_docker_compose_pause_unpause():
    docker.compose.up(detach=True)
    docker.compose.pause()
    for container in docker.compose.ps():
        assert container.state.paused

    docker.compose.unpause()
    for container in docker.compose.ps():
        assert not container.state.paused

    docker.compose.pause(["my_service", "busybox"])

    assert docker.container.inspect("components_my_service_1").state.paused
    assert docker.container.inspect("components_busybox_1").state.paused

    docker.compose.down()


def test_docker_compose_create_down():
    docker.compose.create()
    docker.compose.down()


def test_docker_compose_config():
    compose_config = docker.compose.config()
    assert compose_config.services["alpine"].image == "alpine:latest"

    compose_config = docker.compose.config(return_json=True)
    assert compose_config["services"]["alpine"]["image"] == "alpine:latest"


def test_docker_compose_create_extra_options_down():
    docker.compose.create(build=True, force_recreate=True)
    docker.compose.create(build=True, force_recreate=True)
    docker.compose.create(no_build=True, no_recreate=True)
    docker.compose.down()


def test_docker_compose_up_detach_down_extra_options():
    docker.compose.up(detach=True)
    docker.compose.down(remove_orphans=True, remove_images="all", timeout=3)


def test_docker_compose_up_build():
    docker.compose.up(build=True, detach=True)
    with docker.image.inspect("some_random_image"):
        docker.compose.down()


def test_docker_compose_up_stop_rm():
    docker.compose.up(build=True, detach=True)
    docker.compose.stop(timeout=timedelta(seconds=3))
    docker.compose.rm(volumes=True)


def test_docker_compose_up_rm():
    docker.compose.up(build=True, detach=True)
    docker.compose.rm(stop=True, volumes=True)


def test_docker_compose_up_down_some_services():
    docker.compose.up(["my_service", "busybox"], detach=True)
    docker.compose.down()


def test_docker_compose_ps():
    docker.compose.up(["my_service", "busybox"], detach=True)
    containers = docker.compose.ps()
    names = set(x.name for x in containers)
    assert names == {"components_my_service_1", "components_busybox_1"}
    docker.compose.down()


def test_docker_compose_kill():
    docker.compose.up(["my_service", "busybox"], detach=True)
    names = set(x.name for x in docker.compose.ps())
    assert names == {"components_my_service_1", "components_busybox_1"}

    docker.compose.kill("busybox")

    names = set(x.name for x in docker.compose.ps())
    assert names == {"components_my_service_1"}

    docker.compose.down()


@pytest.mark.skipif(
    True,
    reason="TODO: Fixme. For some reason it works locally but not in "
    "the CI. We get a .dockercfg: $HOME is not defined.",
)
def test_docker_compose_pull():
    try:
        docker.image.remove("busybox")
    except DockerException:
        pass
    try:
        docker.image.remove("alpine")
    except DockerException:
        pass
    docker.compose.pull(["busybox", "alpine"])
    docker.image.inspect(["busybox", "alpine"])


def test_docker_compose_up_abort_on_container_exit():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_ends_quickly.yml"
        ]
    )
    docker.compose.up(["alpine"], abort_on_container_exit=True)
    assert docker.compose.ps() == []
