import time

from docker_cli_wrapper import DockerException, docker
from docker_cli_wrapper.test_utils import random_name


def test_simple_command():
    output = docker.run("hello-world")
    assert "Hello from Docker!" in output


def test_exact_output():
    try:
        docker.image.remove("busybox")
    except DockerException:
        pass
    assert docker.run("busybox", ["echo", "dodo"], remove=True) == "dodo"


def test_remove():
    output = docker.run("hello-world", remove=True)
    assert "Hello from Docker!" in output


def test_cpus():
    output = docker.run("hello-world", cpus=1.5)
    assert "Hello from Docker!" in output


def test_run_volumes():
    volume_name = random_name()
    docker.run(
        "busybox",
        ["touch", "/some/path/dodo"],
        volumes=[(volume_name, "/some/path")],
        remove=True,
    )
    docker.volume.remove(volume_name)


def test_container_remove():
    container = docker.run("hello-world", detach=True)
    time.sleep(0.3)
    assert container in docker.container.list(all=True)
    docker.container.remove(container)
    assert container not in docker.container.list(all=True)


def test_simple_logs():
    container = docker.run("busybox:1", ["echo", "dodo"], detach=True)
    time.sleep(0.3)
    output = docker.container.logs(container)
    assert output == "dodo"


def test_rename():
    name = random_name()
    new_name = random_name()
    assert name != new_name
    container = docker.container.run("hello-world", name=name, detach=True)
    docker.container.rename(container, new_name)

    assert container.name == new_name
    docker.container.remove(container)
