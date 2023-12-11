import json

import pytest

from python_on_whales import docker
from python_on_whales.components.network.cli_wrapper import NetworkInspectResult
from python_on_whales.exceptions import DockerException
from python_on_whales.test_utils import get_all_jsons, random_name


@pytest.mark.parametrize("json_file", get_all_jsons("networks"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    NetworkInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


def test_network_create_remove():
    my_name = random_name()
    with docker.network.create(my_name) as my_network:
        assert my_network.name == my_name


def test_network_create_with_labels():
    my_name = random_name()
    labels = {"hello": "world", "meme": "meme-label"}
    with docker.network.create(my_name, labels=labels) as my_network:
        assert my_network.name == my_name
        for key, value in labels.items():
            assert my_network.labels[key] == value


def test_context_manager():
    with pytest.raises(DockerException):
        with docker.network.create(random_name()) as my_net:
            docker.run(
                "busybox",
                ["ping", "idonotexistatall.com"],
                networks=[my_net],
                remove=True,
            )
            # an exception will be raised because the container will fail
            # but the network will be removed anyway.

    assert my_net not in docker.network.list()


def test_network_connect_disconnect():
    with docker.network.create(random_name()) as my_net:
        with docker.container.run(
            "busybox:1", ["sleep", "infinity"], detach=True
        ) as my_container:
            docker.network.connect(my_net, my_container)
            docker.network.disconnect(my_net, my_container)


def test_remove_nothing():
    all_neworks = set(docker.network.list())
    docker.network.remove([])
    assert all_neworks == set(docker.network.list())


@pytest.mark.usefixtures("swarm_mode")
def test_swarm_service_create():
    with docker.network.create(
        random_name(), attachable=True, driver="overlay"
    ) as my_net:
        with docker.service.create(
            "busybox", ["sleep", "infinity"], network=my_net.name
        ):
            assert len(my_net.containers) == 2  # 1 container + 1 endpoint
