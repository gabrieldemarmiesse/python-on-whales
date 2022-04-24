import pytest

from python_on_whales import docker
from python_on_whales.components.node.models import NodeInspectResult
from python_on_whales.test_utils import get_all_jsons


@pytest.mark.parametrize("json_file", get_all_jsons("nodes"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    a: NodeInspectResult = NodeInspectResult.parse_raw(json_as_txt)
    if json_file.name == "1.json":
        assert (
            a.description.resources.generic_resources[0].named_resource_spec.kind
            == "gpu"
        )
        assert (
            a.description.resources.generic_resources[0].named_resource_spec.value
            == "gpu-0"
        )
        assert a.description.resources.nano_cpus == 4000000001


@pytest.mark.usefixtures("swarm_mode")
def test_list_nodes():
    nodes = docker.node.list()
    assert nodes[0].id[:12] in repr(nodes)
    assert len(nodes) == 1


@pytest.mark.usefixtures("swarm_mode")
def test_tasks():
    service = docker.service.create("busybox", ["sleep", "infinity"])

    current_node = docker.node.list()[0]
    tasks = current_node.ps()
    assert len(tasks) > 0
    assert tasks[0].desired_state == "running"
    docker.service.remove(service)
