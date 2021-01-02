from pathlib import Path

import pytest

from python_on_whales import docker
from python_on_whales.components.context import ContextInspectResult


def get_all_jsons():
    jsons_directory = Path(__file__).parent / "contexts"
    return sorted(list(jsons_directory.iterdir()))


@pytest.mark.parametrize("json_file", get_all_jsons())
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
