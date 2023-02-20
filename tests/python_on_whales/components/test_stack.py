import time
from pathlib import Path

import pytest

from python_on_whales import docker
from python_on_whales.exceptions import NotASwarmManager
from python_on_whales.utils import PROJECT_ROOT


@pytest.fixture
def with_test_stack(swarm_mode):
    time.sleep(1)
    some_stack = docker.stack.deploy(
        "some_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
    )
    time.sleep(1)
    yield some_stack
    some_stack.remove()
    time.sleep(1)


@pytest.mark.usefixtures("with_test_stack")
def test_services_inspect():
    all_services = docker.service.list()
    assert len(all_services) == 4
    assert set(all_services) == set(docker.stack.services("some_stack"))
    assert "name='some_stack'" in repr(docker.stack.list())


@pytest.mark.usefixtures("with_test_stack")
def test_remove_empty_stack_list():
    docker.stack.remove([])
    assert docker.stack.list() != []


def test_stack_ps_and_services(with_test_stack):
    all_services = docker.service.list()

    assert set(all_services) == set(with_test_stack.services())

    stack_tasks = set(docker.stack.ps("some_stack"))
    assert stack_tasks == set(with_test_stack.ps())

    services_tasks = set(docker.service.ps(all_services))
    assert stack_tasks == services_tasks
    assert len(stack_tasks) > 0
    for task in stack_tasks:
        assert task.desired_state == "running"


@pytest.mark.usefixtures("swarm_mode")
def test_stack_variables():
    docker.stack.deploy(
        "other_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
        variables={"SOME_VARIABLE": "hello-world"},
    )

    agent_service = docker.service.inspect("other_stack_agent")
    expected = "SOME_OTHER_VARIABLE=hello-world"
    assert expected in agent_service.spec.task_template.container_spec.env

    docker.stack.remove("other_stack")
    time.sleep(1)


@pytest.mark.usefixtures("swarm_mode")
def test_stack_env_files(tmp_path: Path):
    env_file = tmp_path / "some.env"
    env_file.write_text('SOME_VARIABLE="--tls=true" # some var \n # some comment')
    third_stack = docker.stack.deploy(
        "third_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
        env_files=[env_file],
    )

    agent_service = docker.service.inspect("third_stack_agent")
    expected = 'SOME_OTHER_VARIABLE="--tls=true"'
    assert expected in agent_service.spec.task_template.container_spec.env

    assert docker.stack.list() == [third_stack]
    time.sleep(1)
    docker.stack.remove(third_stack)
    time.sleep(1)


def test_deploy_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.stack.deploy(
            "some_stack",
            [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
        )

    assert "not a swarm manager" in str(e.value).lower()


def test_ps_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.stack.ps("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_list_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.stack.list()

    assert "not a swarm manager" in str(e.value).lower()


def test_remove_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.stack.remove("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_services_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.stack.services("dodo")

    assert "not a swarm manager" in str(e.value).lower()
