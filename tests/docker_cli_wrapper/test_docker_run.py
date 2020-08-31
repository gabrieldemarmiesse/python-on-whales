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
