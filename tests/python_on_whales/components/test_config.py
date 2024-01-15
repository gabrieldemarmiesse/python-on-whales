from pathlib import Path

import pytest

from python_on_whales import DockerClient


@pytest.mark.usefixtures("swarm_mode")
def test_list_configs(docker_client: DockerClient):
    assert docker_client.config.list() == []


@pytest.mark.usefixtures("swarm_mode")
def test_create_delete_config(docker_client: DockerClient, tmp_path: Path):
    config_file = tmp_path / "config.conf"
    config_file.write_text("hello world")
    my_conf = docker_client.config.create("my_conf", config_file)
    with my_conf:
        assert my_conf.spec.name == "my_conf"
        assert docker_client.config.list() == [my_conf]
        assert docker_client.config.inspect("my_conf") == my_conf
        repr(docker_client.config.list())


@pytest.mark.usefixtures("swarm_mode")
def test_labels_config(docker_client: DockerClient, tmp_path: Path):
    config_file = tmp_path / "config.conf"
    config_file.write_text("hello world")
    my_conf = docker_client.config.create(
        "my_conf", config_file, labels=dict(dodo="dada")
    )
    with my_conf:
        assert my_conf.spec.name == "my_conf"
        assert docker_client.config.list(filters=dict(label="dodo=dada")) == [my_conf]
        assert docker_client.config.list(filters=dict(label="dodo=dadu")) == []


@pytest.mark.usefixtures("swarm_mode")
def test_remove_empty_config_list(docker_client: DockerClient, tmp_path: Path):
    config_file = tmp_path / "config.conf"
    config_file.write_text("hello world")
    with docker_client.config.create("my_conf", config_file) as my_conf:
        assert docker_client.config.list() == [my_conf]
        docker_client.config.remove([])
        assert docker_client.config.list() == [my_conf]
