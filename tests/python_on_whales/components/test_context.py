import json

import pytest

from python_on_whales import DockerClient
from python_on_whales.components.context.models import ContextInspectResult
from python_on_whales.test_utils import get_all_jsons


@pytest.mark.parametrize("json_file", get_all_jsons("contexts"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ContextInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


def test_create_context(docker_client: DockerClient):
    testname = "testpow"
    host = "ssh://test@test.domain"
    description = "Python on whales testing context"

    all_contexts_before = set(docker_client.context.list())
    with docker_client.context.create(
        testname, docker=dict(host=host), description=description
    ) as new_context:
        assert new_context.name == testname
        assert new_context.endpoints["docker"].host == host
        assert new_context.metadata["Description"] == description

        assert new_context not in all_contexts_before

        assert new_context in docker_client.context.list()


def test_inpect(docker_client: DockerClient):
    default_context = docker_client.context.inspect()
    assert default_context.name == "default"
    assert default_context == docker_client.context.inspect("default")
    a, b = docker_client.context.inspect(["default", "default"])
    assert a == b


def test_list_contexts(docker_client: DockerClient):
    assert docker_client.context.list() == [docker_client.context.inspect("default")]


def test_use_context(docker_client: DockerClient):
    docker_client.context.use("default")


def test_use_context_returns(docker_client: DockerClient):
    assert docker_client.context.use("default") == docker_client.context.inspect(
        "default"
    )


def test_remove_empty_context_list(docker_client: DockerClient):
    all_contexts = set(docker_client.context.list())
    docker_client.context.remove([])
    assert all_contexts == set(docker_client.context.list())
