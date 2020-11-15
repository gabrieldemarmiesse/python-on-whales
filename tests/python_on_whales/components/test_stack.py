import pytest

from python_on_whales import docker
from python_on_whales.utils import PROJECT_ROOT


@pytest.fixture
def with_test_stack():
    docker.swarm.init()
    docker.stack.deploy(
        "some_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
    )
    yield
    docker.stack.remove("some_stack")
    docker.swarm.leave(force=True)


@pytest.mark.usefixtures("with_test_stack")
def test_services_inspect():
    all_services = docker.service.list()
    assert len(all_services) == 4
    assert set(all_services) == set(docker.stack.services("some_stack"))


def test_stack_variables():
    docker.swarm.init()
    docker.stack.deploy(
        "some_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
        variables={"SOME_VARIABLE": "hello-world"},
    )

    agent_service = docker.service.inspect("some_stack_agent")
    expected = "SOME_OTHER_VARIABLE=hello-world"
    assert expected in agent_service.spec.task_template.container_spec.env

    docker.stack.remove("some_stack")
    docker.swarm.leave(force=True)
