import json

import pytest

from python_on_whales import docker
from python_on_whales.components.context.models import ContextInspectResult
from python_on_whales.test_utils import get_all_jsons


@pytest.mark.parametrize("json_file", get_all_jsons("contexts"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ContextInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


def test_create_context():
    testname = "testpow"
    host = "ssh://test@test.domain"
    description = "Python on whales testing context"

    all_contexts_before = set(docker.context.list())
    with docker.context.create(
        testname, docker=dict(host=host), description=description
    ) as new_context:
        assert new_context.name == testname
        assert new_context.endpoints["docker"].host == host
        assert new_context.metadata["Description"] == description

        assert new_context not in all_contexts_before

        assert new_context in docker.context.list()


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


def test_use_context_returns():
    assert docker.context.use("default") == docker.context.inspect("default")


def test_remove_empty_context_list():
    all_contexts = set(docker.context.list())
    docker.context.remove([])
    assert all_contexts == set(docker.context.list())
