import time
from datetime import timedelta
from pathlib import Path

import pytest

import python_on_whales
from python_on_whales import DockerClient
from python_on_whales.components.compose.models import ComposeConfig
from python_on_whales.exceptions import NoSuchImage
from python_on_whales.test_utils import get_all_jsons
from python_on_whales.utils import PROJECT_ROOT

pytestmark = pytest.mark.skipif(
    not python_on_whales.docker.compose.is_installed(),
    reason="Those tests need docker compose.",
)

docker = DockerClient(
    compose_files=[PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"]
)


def test_compose_project_name():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
        ],
        compose_project_name="dudu",
    )
    docker.compose.up(["busybox", "alpine"], detach=True)
    containers = docker.compose.ps()
    container_names = set(x.name for x in containers)
    assert container_names == {"dudu_busybox_1", "dudu_alpine_1"}
    docker.compose.down()


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
    docker.compose.down()


def test_no_containers():
    assert docker.compose.ps() == []


def test_docker_compose_up_detach_down():
    docker.compose.up(["my_service", "busybox", "alpine"], detach=True)
    docker.compose.down()


def test_docker_compose_up_detach_down_with_scales():
    docker.compose.up(
        ["my_service", "busybox", "alpine"],
        detach=True,
        scales={"busybox": 2, "alpine": 3},
    )
    assert len(docker.compose.ps()) == 6

    docker.compose.up(
        ["my_service", "busybox", "alpine"],
        detach=True,
        scales={"busybox": 2, "alpine": 5},
    )
    assert len(docker.compose.ps()) == 8

    docker.compose.down(timeout=1)


def test_docker_compose_pause_unpause():
    docker.compose.up(["my_service", "busybox", "alpine"], detach=True)
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
    docker.compose.up(["my_service", "busybox", "alpine"], detach=True)
    docker.compose.down(remove_orphans=True, remove_images="all", timeout=3)


def test_docker_compose_up_build():
    docker.compose.up(["my_service", "busybox", "alpine"], build=True, detach=True)
    with docker.image.inspect("some_random_image"):
        docker.compose.down()


def test_docker_compose_up_stop_rm():
    docker.compose.up(["my_service", "busybox", "alpine"], build=True, detach=True)
    docker.compose.stop(timeout=timedelta(seconds=3))
    docker.compose.rm(volumes=True)


def test_docker_compose_up_rm():
    docker.compose.up(["my_service", "busybox", "alpine"], build=True, detach=True)
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

    for container in docker.compose.ps():
        assert container.state.running

    docker.compose.kill("busybox")

    assert not docker.container.inspect("components_busybox_1").state.running

    docker.compose.down()


@pytest.mark.skipif(
    True,
    reason="TODO: Fixme. For some reason it works locally but not in "
    "the CI. We get a .dockercfg: $HOME is not defined.",
)
def test_docker_compose_pull():
    try:
        docker.image.remove("busybox")
    except NoSuchImage:
        pass
    try:
        docker.image.remove("alpine")
    except NoSuchImage:
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
    for container in docker.compose.ps():
        assert not container.state.running
    docker.compose.down()


def test_passing_env_files(tmp_path: Path):
    compose_env_file = tmp_path / "dodo.env"
    compose_env_file.write_text("SOME_VARIABLE_TO_INSERT=hello\n")
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_ends_quickly.yml"
        ],
        compose_env_file=compose_env_file,
    )
    output = docker.compose.config()

    assert output.services["alpine"].environment["SOME_VARIABLE"] == "hello"


def test_entrypoint_loaded_in_config():
    assert docker.compose.config().services["dodo"].entrypoint == ["/bin/dudu"]


def test_config_complexe_compose():
    """Checking that the pydantic model does its job"""
    compose_file = (
        PROJECT_ROOT / "tests/python_on_whales/components/complexe-compose.yml"
    )
    docker = DockerClient(compose_files=[compose_file])
    config = docker.compose.config()

    assert (
        config.services["my_service"].build.context
        == (compose_file.parent / "my_service_build").absolute()
    )
    assert config.services["my_service"].image == "some_random_image"
    assert config.services["my_service"].command == [
        "ping",
        "-c",
        "2",
        "www.google.com",
    ]

    assert config.services["my_service"].ports[0].published == 5000
    assert config.services["my_service"].ports[0].target == 5000

    assert config.services["my_service"].volumes[0].source == "/tmp"
    assert config.services["my_service"].volumes[0].target == "/tmp"
    assert config.services["my_service"].volumes[1].source == "dodo"
    assert config.services["my_service"].volumes[1].target == "/dodo"

    assert config.services["my_service"].environment == {"DATADOG_HOST": "something"}
    assert config.services["my_service"].deploy.placement.constraints == [
        "node.labels.hello-world == yes"
    ]
    assert config.services["my_service"].deploy.resources.limits.cpus == 2
    assert config.services["my_service"].deploy.resources.limits.memory == 41943040

    assert config.services["my_service"].deploy.resources.reservations.cpus == 1
    assert (
        config.services["my_service"].deploy.resources.reservations.memory == 20971520
    )

    assert config.services["my_service"].deploy.replicas == 4

    assert not config.volumes["dodo"].external


def test_compose_down_volumes():
    compose_file = (
        PROJECT_ROOT / "tests/python_on_whales/components/complexe-compose.yml"
    )
    docker = DockerClient(compose_files=[compose_file])
    docker.compose.up(
        ["my_service"], detach=True, scales=dict(my_service=1), build=True
    )
    assert docker.volume.exists("components_dodo")
    docker.compose.down()
    assert docker.volume.exists("components_dodo")
    docker.compose.down(volumes=True)
    assert not docker.volume.exists("components_dodo")


def test_compose_config_from_rc1():
    config = ComposeConfig.parse_file(
        Path(__file__).parent / "strange_compose_config_rc1.json"
    )

    assert config.services["myservice"].deploy.resources.reservations.cpus == "'0.25'"


@pytest.mark.parametrize("json_file", get_all_jsons("compose"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    config: ComposeConfig = ComposeConfig.parse_raw(json_as_txt)
    if json_file.name == "0.json":
        assert config.services["traefik"].labels["traefik.enable"] == "true"


def test_compose_run_simple():
    result = docker.compose.run("alpine", ["echo", "dodo"], remove=True)
    assert result == "dodo"


def test_compose_run_detach():
    container = docker.compose.run("alpine", ["echo", "dodo"], detach=True)

    time.sleep(0.1)
    assert not container.state.running
    assert container.logs() == "dodo\n"


def test_compose_version():
    assert "Docker Compose version v2" in docker.compose.version()
