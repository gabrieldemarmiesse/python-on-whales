import time

import pytest

from python_on_whales import docker
from python_on_whales.components.service.models import ServiceInspectResult
from python_on_whales.exceptions import NoSuchService
from python_on_whales.test_utils import get_all_jsons


@pytest.mark.parametrize("json_file", get_all_jsons("services"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ServiceInspectResult.parse_raw(json_as_txt)
    # we could do more checks here if needed


@pytest.mark.usefixtures("swarm_mode")
def test_tasks():
    service = docker.service.create("busybox", ["sleep", "infinity"])

    tasks = service.ps()
    assert len(tasks) > 0
    assert tasks[0].desired_state == "running"
    docker.service.remove(service)


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
def test_inspect_no_such_service(docker_function):
    with pytest.raises(NoSuchService):
        docker.service.inspect("DOODODGOIHURHURI")


@pytest.mark.usefixtures("swarm_mode")
def test_scale_no_such_service():
    with pytest.raises(NoSuchService):
        docker.service.scale({"DOODODGOIHURHURI": 14})
