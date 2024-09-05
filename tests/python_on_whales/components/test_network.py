import json

import pytest

from python_on_whales import DockerClient
from python_on_whales.components.network.cli_wrapper import NetworkInspectResult
from python_on_whales.exceptions import DockerException
from python_on_whales.test_utils import get_all_jsons, random_name


@pytest.mark.parametrize("json_file", get_all_jsons("networks"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    NetworkInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_network_create_remove(ctr_client: DockerClient):
    my_name = random_name()
    with ctr_client.network.create(my_name) as my_network:
        assert my_network.name == my_name


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_network_create_with_labels(ctr_client: DockerClient):
    my_name = random_name()
    labels = {"hello": "world", "meme": "meme-label"}
    with ctr_client.network.create(my_name, labels=labels) as my_network:
        assert my_network.name == my_name
        for key, value in labels.items():
            assert my_network.labels[key] == value


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_context_manager(ctr_client: DockerClient):
    with pytest.raises(DockerException):
        with ctr_client.network.create(random_name()) as my_net:
            ctr_client.run(
                "busybox",
                ["ping", "idonotexistatall.com"],
                networks=[my_net],
                remove=True,
            )
            # an exception will be raised because the container will fail
            # but the network will be removed anyway.

    assert my_net not in ctr_client.network.list()


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_network_connect_disconnect(ctr_client: DockerClient):
    with ctr_client.network.create(random_name()) as my_net:
        with ctr_client.container.run(
            "busybox:1", ["sleep", "infinity"], detach=True
        ) as my_container:
            ctr_client.network.connect(my_net, my_container)
            ctr_client.network.disconnect(my_net, my_container)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_remove_nothing(ctr_client: DockerClient):
    all_neworks = set(ctr_client.network.list())
    ctr_client.network.remove([])
    assert all_neworks == set(ctr_client.network.list())


@pytest.mark.usefixtures("swarm_mode")
def test_swarm_service_create(docker_client: DockerClient):
    with docker_client.network.create(
        random_name(), attachable=True, driver="overlay"
    ) as my_net:
        with docker_client.service.create(
            "busybox", ["sleep", "infinity"], network=my_net.name
        ):
            assert len(my_net.containers) == 2  # 1 container + 1 endpoint


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_network_exists(ctr_client: DockerClient):
    network_name = random_name()
    assert not ctr_client.network.exists(network_name)
    with ctr_client.network.create(network_name) as network:
        assert ctr_client.network.exists(network_name)
        assert ctr_client.network.exists(network)
        assert network.exists()

    # Outside with clause, network should be removed and no longer exist
    assert not ctr_client.network.exists(network)
    assert not network.exists()
