import pytest

from python_on_whales import docker
from python_on_whales.components.context.models import ContextInspectResult
from python_on_whales.test_utils import get_all_jsons


@pytest.mark.parametrize("json_file", get_all_jsons("contexts"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ContextInspectResult.parse_raw(json_as_txt)
    # we could do more checks here if needed


def test_inpect():
    default_context = docker.context.inspect()
    assert default_context.name == "default"
    assert default_context == docker.context.inspect("default")
    a, b = docker.context.inspect(["default", "default"])
    assert a == b


def test_list_contexts():
    assert docker.context.list() == [docker.context.inspect("default")]


def test_use_context():
    docker.context.use("default")


def test_remove_empty_context_list():
    all_contexts = set(docker.context.list())
    docker.context.remove([])
    assert all_contexts == set(docker.context.list())
