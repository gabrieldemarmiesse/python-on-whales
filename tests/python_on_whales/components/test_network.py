from python_on_whales import docker
from python_on_whales.test_utils import random_name


def test_network_create_remove():
    my_name = random_name()
    my_network = docker.network.create(my_name)
    assert my_network.name == my_name
    docker.network.remove(my_name)
