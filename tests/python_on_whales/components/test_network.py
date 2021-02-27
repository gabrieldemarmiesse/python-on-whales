import pytest

from python_on_whales import DockerException, docker
from python_on_whales.components.network.models import NetworkInspectResult
from python_on_whales.test_utils import get_all_jsons, random_name


@pytest.mark.parametrize("json_file", get_all_jsons("networks"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    NetworkInspectResult.parse_raw(json_as_txt)
    # we could do more checks here if needed


def test_network_create_remove():
    my_name = random_name()
    my_network = docker.network.create(my_name)
    assert my_network.name == my_name
    docker.network.remove(my_name)


def test_context_manager():
    from python_on_whales import docker

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
