import json
import tempfile
import time

import pytest

from python_on_whales import DockerClient
from python_on_whales.components.service.models import ServiceInspectResult
from python_on_whales.exceptions import NoSuchService, NotASwarmManager
from python_on_whales.test_utils import get_all_jsons


@pytest.mark.parametrize("json_file", get_all_jsons("services"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ServiceInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


@pytest.mark.usefixtures("swarm_mode")
def test_tasks(ctr_client: DockerClient):
    service = ctr_client.service.create("busybox", ["sleep", "infinity"])

    tasks = service.ps()
    assert len(tasks) > 0
    assert tasks[0].desired_state == "running"
    ctr_client.service.remove(service)


@pytest.mark.usefixtures("swarm_mode")
def test_get_logs(ctr_client: DockerClient):
    with ctr_client.service.create(
        "busybox", ["sh", "-c", "echo dodo && sleep infinity"]
    ) as my_service:
        assert my_service.ps()[0].desired_state == "running"
        assert ctr_client.service.logs(my_service).split("|")[-1].strip() == "dodo"


@pytest.mark.usefixtures("swarm_mode")
def test_get_list_of_services(ctr_client: DockerClient):
    with ctr_client.service.create(
        "busybox", ["sh", "-c", "echo dodo && sleep infinity"]
    ) as my_service:
        list_of_services = ctr_client.service.list()
        assert [my_service] == list_of_services


@pytest.mark.usefixtures("swarm_mode")
def test_get_list_of_services_no_services(ctr_client: DockerClient):
    assert ctr_client.service.list() == []


@pytest.mark.usefixtures("swarm_mode")
def test_remove_empty_services_list(ctr_client: DockerClient):
    with ctr_client.service.create(
        "busybox", ["sh", "-c", "echo dodo && sleep infinity"]
    ) as my_service:
        assert my_service in ctr_client.service.list()
        set_services = set(ctr_client.service.list())
        ctr_client.service.remove([])
        assert set(ctr_client.service.list()) == set_services


@pytest.mark.usefixtures("swarm_mode")
def test_service_scale(ctr_client: DockerClient):
    service = ctr_client.service.create("busybox", ["sleep", "infinity"])
    service.scale(3)
    time.sleep(0.4)
    assert service.spec.mode["Replicated"] == {"Replicas": 3}
    service.update(replicas=1)
    time.sleep(0.4)
    assert service.spec.mode["Replicated"] == {"Replicas": 1}


@pytest.mark.usefixtures("swarm_mode")
def test_context_manager(ctr_client: DockerClient):
    with pytest.raises(RuntimeError):
        with ctr_client.service.create("busybox", ["sleep", "infinity"]) as my_service:
            assert my_service.spec.task_template.container_spec.image.startswith(
                "busybox"
            )
            assert my_service.exists()
            raise RuntimeError

    assert not my_service.exists()


@pytest.mark.usefixtures("swarm_mode")
def test_service_restart(ctr_client: DockerClient):
    my_service = ctr_client.service.create(
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
def test_service_secrets(ctr_client: DockerClient):
    secret_user = None
    secret_pass = None
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"supersecretuser")
        f.seek(0)
        secret_user = ctr_client.secret.create("dbuser", f.name)
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"supersecretpass")
        f.seek(0)
        secret_pass = ctr_client.secret.create("dbpass", f.name)

    with ctr_client.service.create(
        "ubuntu",
        ["bash", "-c", "cat /run/secrets/{dbuser,dbpass} && sleep infinity"],
        secrets=[
            {
                "source": "dbuser",
            },
            {
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
def test_service_mounts(ctr_client: DockerClient):
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"config")
        f.seek(0)
        with ctr_client.service.create(
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


@pytest.mark.usefixtures("swarm_mode")
def test_inspect_no_such_service(ctr_client: DockerClient):
    with pytest.raises(NoSuchService):
        ctr_client.service.inspect("DOODODGOIHURHURI")


@pytest.mark.usefixtures("swarm_mode")
def test_remove_no_such_service(ctr_client: DockerClient):
    with pytest.raises(NoSuchService):
        ctr_client.service.remove("DOODODGOIHURHURI")


@pytest.mark.usefixtures("swarm_mode")
def test_ps_no_such_service(ctr_client: DockerClient):
    with pytest.raises(NoSuchService):
        ctr_client.service.ps("DOODODGOIHURHURI")


@pytest.mark.usefixtures("swarm_mode")
def test_scale_no_such_service(ctr_client: DockerClient):
    with pytest.raises(NoSuchService):
        ctr_client.service.scale({"DOODODGOIHURHURI": 14})


def test_create_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.service.create("busybox", ["sleep", "infinity"])

    assert "not a swarm manager" in str(e.value).lower()


def test_inspect_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.service.inspect("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_exists_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.service.exists("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_list_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.service.list()

    assert "not a swarm manager" in str(e.value).lower()


def test_ps_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.service.ps("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_remove_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.service.remove("dodo")

    assert "not a swarm manager" in str(e.value).lower()


def test_scale_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.service.scale({"dodo": 8})

    assert "not a swarm manager" in str(e.value).lower()


def test_update_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.service.update("dodo", image="busybox")

    assert "not a swarm manager" in str(e.value).lower()
