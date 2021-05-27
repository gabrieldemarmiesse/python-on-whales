from pathlib import Path

import pytest

from python_on_whales import DockerException, docker


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
    docker.pull(f"{docker_registry_without_login}/my_busybox")
    docker.logout(docker_registry_without_login)
    assert (
        docker_registry_without_login
        not in (Path.home() / ".docker" / "config.json").read_text()
    )
