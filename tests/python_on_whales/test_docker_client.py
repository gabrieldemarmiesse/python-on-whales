from pathlib import Path

import pytest

from python_on_whales import DockerException, docker


def test_login_logout(tmp_path):
    encrypted_password = docker.run(
        "mhenry07/apache2-utils",
        ["htpasswd", "-Bbn", "my_user", "my_password"],
        remove=True,
    )
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
    registry.copy_to(htpasswd_file, "/tmp/htpasswd")
    registry.start()
    busybox_image = docker.pull("busybox")
    busybox_image.tag("localhost:5000/my_busybox")
    with pytest.raises(DockerException):
        docker.push("localhost:5000/my_busybox")
    docker.login("localhost:5000", username="my_user", password="my_password")
    assert "localhost:5000" in (Path.home() / ".docker" / "config.json").read_text()
    docker.push("localhost:5000/my_busybox")
    busybox_image.remove(force=True)
    docker.pull("localhost:5000/my_busybox")
    docker.logout("localhost:5000")
    assert "localhost:5000" not in (Path.home() / ".docker" / "config.json").read_text()
