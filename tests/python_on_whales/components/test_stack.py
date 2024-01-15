import time
from pathlib import Path
from typing import Generator

import pytest

from python_on_whales import DockerClient
from python_on_whales.components.stack.cli_wrapper import Stack
from python_on_whales.exceptions import NotASwarmManager
from python_on_whales.utils import PROJECT_ROOT


@pytest.fixture
def stack(
    docker_client: DockerClient, swarm_mode: None
) -> Generator[Stack, None, None]:
    time.sleep(1)
    some_stack = docker_client.stack.deploy(
        "some_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
    )
    time.sleep(1)
    yield some_stack
    some_stack.remove()
    time.sleep(1)


@pytest.mark.usefixtures("stack")
def test_services_inspect(docker_client: DockerClient):
    all_services = docker_client.service.list()
    assert len(all_services) == 4
    assert set(all_services) == set(docker_client.stack.services("some_stack"))
    assert "name='some_stack'" in repr(docker_client.stack.list())


@pytest.mark.usefixtures("stack")
def test_remove_empty_stack_list(docker_client: DockerClient):
    docker_client.stack.remove([])
    assert docker_client.stack.list() != []


def test_stack_ps_and_services(docker_client: DockerClient, stack: Stack):
    all_services = docker_client.service.list()

    assert set(all_services) == set(stack.services())

    stack_tasks = set(docker_client.stack.ps("some_stack"))
    assert stack_tasks == set(stack.ps())

    services_tasks = set(docker_client.service.ps(all_services))
    assert stack_tasks == services_tasks
    assert len(stack_tasks) > 0
    for task in stack_tasks:
        assert task.desired_state == "running"


@pytest.mark.usefixtures("swarm_mode")
def test_stack_variables(docker_client: DockerClient):
    docker_client.stack.deploy(
        "other_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
        variables={"SOME_VARIABLE": "hello-world"},
    )

    agent_service = docker_client.service.inspect("other_stack_agent")
    expected = "SOME_OTHER_VARIABLE=hello-world"
    assert expected in agent_service.spec.task_template.container_spec.env

    docker_client.stack.remove("other_stack")
    time.sleep(1)


@pytest.mark.usefixtures("swarm_mode")
def test_stack_env_files(docker_client: DockerClient, tmp_path: Path):
    env_file = tmp_path / "some.env"
    env_file.write_text('SOME_VARIABLE="--tls=true" # some var \n # some comment')
    third_stack = docker_client.stack.deploy(
        "third_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
        env_files=[env_file],
    )

    agent_service = docker_client.service.inspect("third_stack_agent")
    expected = 'SOME_OTHER_VARIABLE="--tls=true"'
    assert expected in agent_service.spec.task_template.container_spec.env

    assert docker_client.stack.list() == [third_stack]
    time.sleep(1)
    docker_client.stack.remove(third_stack)
    time.sleep(1)


def test_deploy_not_swarm_manager(docker_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        docker_client.stack.deploy(
            "some_stack",
            [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
        )

    assert "not a swarm manager" in str(e.value).lower()


def test_ps_not_swarm_manager(docker_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        docker_client.stack.ps("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_list_not_swarm_manager(docker_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        docker_client.stack.list()

    assert "not a swarm manager" in str(e.value).lower()


def test_remove_not_swarm_manager(docker_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        docker_client.stack.remove("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_services_not_swarm_manager(docker_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        docker_client.stack.services("dodo")

    assert "not a swarm manager" in str(e.value).lower()
