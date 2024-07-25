import re
import time
from pathlib import Path

import pytest

from python_on_whales import DockerClient
from python_on_whales.exceptions import DockerException


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_version(ctr_client: DockerClient):
    version_info = ctr_client.version()
    assert re.match(r"\d+\.\d+", version_info.client.version)
    if ctr_client.client_config.client_type == "docker":
        assert re.match(r"\d+\.\d+", version_info.server.version)


def test_login_logout(docker_client: DockerClient, docker_registry_without_login: str):
    busybox_image = docker_client.pull("busybox")
    busybox_image.tag(f"{docker_registry_without_login}/my_busybox")
    with pytest.raises(DockerException):
        docker_client.push(f"{docker_registry_without_login}/my_busybox")
    docker_client.login(
        docker_registry_without_login, username="my_user", password="my_password"
    )
    assert (
        docker_registry_without_login
        in (Path.home() / ".docker" / "config.json").read_text()
    )
    docker_client.push(f"{docker_registry_without_login}/my_busybox")
    docker_client.push(
        [f"{docker_registry_without_login}/my_busybox" for _ in range(2)]
    )
    docker_client.pull(f"{docker_registry_without_login}/my_busybox")
    docker_client.logout(docker_registry_without_login)
    assert (
        docker_registry_without_login
        not in (Path.home() / ".docker" / "config.json").read_text()
    )


@pytest.mark.skipif(True, reason="It doesn't work in the ci")
def test_docker_client_options(docker_client: DockerClient):
    if docker_client.container.exists("test_dind_container"):
        docker_client.container.remove("test_dind_container", force=True, volumes=True)

    with docker_client.run(
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
