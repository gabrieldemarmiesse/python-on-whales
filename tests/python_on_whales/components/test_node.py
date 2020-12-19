from pathlib import Path
from typing import List

import pytest

from python_on_whales import docker
from python_on_whales.components.node import NodeInspectResult


def get_all_nodes_jsons() -> List[Path]:
    jsons_directory = Path(__file__).parent / "nodes"
    return sorted(list(jsons_directory.iterdir()))


@pytest.fixture
def with_swarm():
    docker.swarm.init()
    yield
    docker.swarm.leave(force=True)


@pytest.mark.usefixtures("with_swarm")
def test_list_nodes():
    nodes = docker.node.list()
    assert len(nodes) == 1


@pytest.mark.parametrize("json_file", get_all_nodes_jsons())
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
