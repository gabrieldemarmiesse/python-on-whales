import time
from pathlib import Path

import pytest

from python_on_whales import DockerClient, docker
from python_on_whales.exceptions import DockerException


def test_login_logout(docker_registry_without_login):
    busybox_image = docker.pull("busybox")
    busybox_image.tag(f"{docker_registry_without_login}/my_busybox")
    with pytest.raises(DockerException):
        docker.push(f"{docker_registry_without_login}/my_busybox")
    docker.login(
        docker_registry_without_login, username="my_user", password="my_password"
    )
    assert (
        docker_registry_without_login
        in (Path.home() / ".docker" / "config.json").read_text()
    )
    docker.push(f"{docker_registry_without_login}/my_busybox")
    docker.push([f"{docker_registry_without_login}/my_busybox" for _ in range(2)])
    docker.pull(f"{docker_registry_without_login}/my_busybox")
    docker.logout(docker_registry_without_login)
    assert (
        docker_registry_without_login
        not in (Path.home() / ".docker" / "config.json").read_text()
    )


@pytest.mark.skipif(True, reason="It doesn't work in the ci")
def test_docker_client_options():
    if docker.container.exists("test_dind_container"):
        docker.container.remove("test_dind_container", force=True, volumes=True)

    with docker.run(
        "docker:20.10.16-dind",
        ["dockerd", "--host=tcp://0.0.0.0:2375", "--tls=false"],
        remove=True,
        privileged=True,
        publish=[(2380, 2375)],
        detach=True,
        name="test_dind_container",
    ):
        time.sleep(10)
        dind_client = DockerClient(host="tcp://localhost:2380")
        assert dind_client.image.list() == []
        assert "Hello from Docker!" in dind_client.run("hello-world")

        dind_client = DockerClient(
            client_call=["docker", "--host=tcp://localhost:2380"]
        )
        assert "Hello from Docker!" in dind_client.run("hello-world")
