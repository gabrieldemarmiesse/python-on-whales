import pytest

from python_on_whales import docker


@pytest.mark.usefixtures("swarm_mode")
def test_list_configs():
    assert docker.config.list() == []


@pytest.mark.usefixtures("swarm_mode")
def test_create_delete_config(tmp_path):
    config_file = tmp_path / "config.conf"
    config_file.write_text("hello world")
    my_conf = docker.config.create("my_conf", config_file)
    assert my_conf.spec.name == "my_conf"
    assert docker.config.list() == [my_conf]
    assert docker.config.inspect("my_conf") == my_conf
    my_conf.remove()
