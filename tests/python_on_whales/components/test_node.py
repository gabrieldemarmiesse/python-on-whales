import pytest

from python_on_whales import docker


@pytest.fixture
def with_swarm():
    docker.swarm.init()
    yield
    docker.swarm.leave(force=True)


@pytest.mark.usefixtures("with_swarm")
def test_list_nodes():
    nodes = docker.node.list()
    assert len(nodes) == 1
