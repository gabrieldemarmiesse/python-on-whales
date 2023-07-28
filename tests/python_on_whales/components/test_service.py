import json
import time

import pytest

from python_on_whales import docker
from python_on_whales.components.service.models import ServiceInspectResult
from python_on_whales.exceptions import NoSuchService, NotASwarmManager
from python_on_whales.test_utils import get_all_jsons


@pytest.mark.parametrize("json_file", get_all_jsons("services"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ServiceInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


@pytest.mark.usefixtures("swarm_mode")
def test_tasks():
    service = docker.service.create("busybox", ["sleep", "infinity"])

    tasks = service.ps()
    assert len(tasks) > 0
    assert tasks[0].desired_state == "running"
    docker.service.remove(service)


@pytest.mark.usefixtures("swarm_mode")
def test_get_logs():
    with docker.service.create(
        "busybox", ["sh", "-c", "echo dodo && sleep infinity"]
    ) as my_service:
        assert my_service.ps()[0].desired_state == "running"
        assert docker.service.logs(my_service).split("|")[-1].strip() == "dodo"


@pytest.mark.usefixtures("swarm_mode")
def test_get_list_of_services():
    with docker.service.create(
        "busybox", ["sh", "-c", "echo dodo && sleep infinity"]
    ) as my_service:
        list_of_services = docker.service.list()
        assert [my_service] == list_of_services


@pytest.mark.usefixtures("swarm_mode")
def test_get_list_of_services_no_services():
    assert docker.service.list() == []


@pytest.mark.usefixtures("swarm_mode")
def test_remove_empty_services_list():
    with docker.service.create(
        "busybox", ["sh", "-c", "echo dodo && sleep infinity"]
    ) as my_service:
        assert my_service in docker.service.list()
        set_services = set(docker.service.list())
        docker.service.remove([])
        assert set(docker.service.list()) == set_services


@pytest.mark.usefixtures("swarm_mode")
def test_service_scale():
    service = docker.service.create("busybox", ["sleep", "infinity"])
    service.scale(3)
    time.sleep(0.4)
    assert service.spec.mode["Replicated"] == {"Replicas": 3}


@pytest.mark.usefixtures("swarm_mode")
def test_context_manager():
    with pytest.raises(RuntimeError):
        with docker.service.create("busybox", ["sleep", "infinity"]) as my_service:
            assert my_service.spec.task_template.container_spec.image.startswith(
                "busybox"
            )
            assert my_service.exists()
            raise RuntimeError

    assert not my_service.exists()


@pytest.mark.parametrize(
    "docker_function",
    [docker.service.inspect, docker.service.remove, docker.service.ps],
)
@pytest.mark.usefixtures("swarm_mode")
def test_some_functions_no_such_service(docker_function):
    with pytest.raises(NoSuchService):
        docker_function("DOODODGOIHURHURI")


@pytest.mark.usefixtures("swarm_mode")
def test_scale_no_such_service():
    with pytest.raises(NoSuchService):
        docker.service.scale({"DOODODGOIHURHURI": 14})


def test_create_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.service.create("busybox", ["sleep", "infinity"])

    assert "not a swarm manager" in str(e.value).lower()


def test_inspect_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.service.inspect("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_exists_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.service.exists("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_list_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.service.list()

    assert "not a swarm manager" in str(e.value).lower()


def test_ps_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.service.ps("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_remove_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.service.remove("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_scale_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.service.scale({"dodo": 8})

    assert "not a swarm manager" in str(e.value).lower()


def test_update_not_swarm_manager():
    with pytest.raises(NotASwarmManager) as e:
        docker.service.update("dodo", image="busybox")

    assert "not a swarm manager" in str(e.value).lower()
