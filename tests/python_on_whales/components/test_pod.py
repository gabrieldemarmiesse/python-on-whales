import json
from pathlib import Path

import pytest

from python_on_whales import DockerClient
from python_on_whales.components.pod.models import PodInspectResult
from python_on_whales.exceptions import NoSuchPod
from python_on_whales.test_utils import get_all_jsons, random_name


@pytest.mark.parametrize("json_file", get_all_jsons("pods"))
def test_load_json(json_file: Path):
    json_as_txt = json_file.read_text()
    PodInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


def test_create_simple(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name) as pod:
        assert pod.exists()
        assert pod.name == pod_name
        assert pod.state.lower() == "created"
    assert not pod.exists()


def test_start_simple(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name) as pod:
        pod.start()
        assert pod.state.lower() == "running"
    assert not pod.exists()


def test_stop_simple(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name) as pod:
        pod.start()
        assert pod.state.lower() == "running"
        pod.stop()
        assert pod.state.lower() == "exited"
    assert not pod.exists()


def test_inspect(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name) as pod:
        inspected_pod = podman_client.pod.inspect(pod_name)
        assert inspected_pod == pod
        assert inspected_pod.name == pod_name


def test_list_multiple(podman_client: DockerClient):
    pod1_name = random_name()
    pod2_name = random_name()
    with podman_client.pod.create(pod1_name), podman_client.pod.create(pod2_name):
        listed_pods = podman_client.pod.list()
        listed_pod_names = [p.name for p in listed_pods]
        assert pod1_name in listed_pod_names
        assert pod2_name in listed_pod_names


def test_does_not_exist(podman_client: DockerClient):
    assert podman_client.pod.exists("pod-that-does-not-exist") is False


def test_create_with_container(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name, infra=True) as pod:
        ubuntu_container = podman_client.container.create("ubuntu", pod=pod)
        assert pod.num_containers == 2
        assert ubuntu_container.id in [ctr.id for ctr in pod.containers]
    assert not pod.exists()
    assert not ubuntu_container.exists()


def test_start_with_container(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name, infra=True) as pod:
        ubuntu_container = podman_client.container.create(
            "ubuntu", ["sleep", "infinity"], pod=pod
        )
        assert ubuntu_container.state.running is False
        pod.start()
        ubuntu_container.reload()
        assert ubuntu_container.state.running is True
    assert not pod.exists()
    assert not ubuntu_container.exists()


def test_kill_with_container(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name, infra=True) as pod:
        ubuntu_container = podman_client.container.create(
            "ubuntu", ["sleep", "infinity"], pod=pod
        )
        assert ubuntu_container.state.running is False
        pod.start()
        ubuntu_container.reload()
        assert ubuntu_container.state.running is True
        pod.kill()
        assert ubuntu_container.state.running is False
    assert not pod.exists()
    assert not ubuntu_container.exists()


@pytest.mark.parametrize(
    "method",
    ["inspect", "kill", "logs", "remove", "restart", "start", "stop"],
)
def test_functions_nosuchpod(method: str, podman_client: DockerClient):
    with pytest.raises(NoSuchPod):
        getattr(podman_client.pod, method)("pod-that-does-not-exist")
