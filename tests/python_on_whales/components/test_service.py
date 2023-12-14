import json
import tempfile
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
    service.update(replicas=1)
    time.sleep(0.4)
    assert service.spec.mode["Replicated"] == {"Replicas": 1}


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


@pytest.mark.usefixtures("swarm_mode")
def test_service_restart():
    my_service = docker.service.create(
        "busybox",
        ["echo", "Hello"],
        detach=True,
        restart_condition="none",
        restart_max_attempts=0,
    )
    time.sleep(2)
    assert my_service.ps()[0].desired_state == "shutdown"
    my_service.remove()


@pytest.mark.usefixtures("swarm_mode")
def test_service_secrets():
    secret_user = None
    secret_pass = None
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"supersecretuser")
        f.seek(0)
        secret_user = docker.secret.create("dbuser", f.name)
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"supersecretpass")
        f.seek(0)
        secret_pass = docker.secret.create("dbpass", f.name)

    with docker.service.create(
        "ubuntu",
        ["bash", "-c", "cat /run/secrets/{dbuser,dbpass} && sleep infinity"],
        secrets=[
            {
                "source": "dbuser",
            },
            {
                "source": "dbpass",
                "source": "dbpass",
                "uid": "1000",
                "gid": "1000",
                "mode": "0400",
            },
        ],
    ) as my_service:
        assert my_service.ps()[0].desired_state == "running"
    secret_user.remove()
    secret_pass.remove()


@pytest.mark.usefixtures("swarm_mode")
def test_service_mounts():
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"config")
        f.seek(0)
        with docker.service.create(
            "ubuntu",
            ["bash", "-c", f"cat {f.name} && sleep infinity"],
            mounts=[
                {
                    "type": "bind",
                    "source": f.name,
                    "destination": f.name,
                },
            ],
        ) as my_service:
            assert my_service.ps()[0].desired_state == "running"


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
