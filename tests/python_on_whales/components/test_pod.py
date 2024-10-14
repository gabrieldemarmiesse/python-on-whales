import json
import re
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


def test_create_devices_arg(podman_client: DockerClient):
    # Should skip if podman version is below 4.0 (need to implement
    # DockerClient.version).
    pod_name = random_name()
    with podman_client.pod.create(pod_name, devices=["/dev/net/tun"]) as pod:
        output = podman_client.container.run(
            "ubuntu", ["find", "/dev/", "-name", "tun"], pod=pod
        )
        assert "/dev/net/tun" in output


def test_create_dns_arg(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name, dns=["1.2.3.4"]) as pod:
        output = podman_client.container.run(
            "ubuntu", ["cat", "/etc/resolv.conf"], pod=pod
        )
        assert "1.2.3.4" in output


def test_create_exit_policy_arg(podman_client: DockerClient):
    # Should skip if podman version is below 4.2 (need to implement
    # DockerClient.version).
    pod_name = random_name()
    with podman_client.pod.create(pod_name, exit_policy="stop") as pod:
        assert pod.state == "Created"
        podman_client.container.run("ubuntu", ["true"], pod=pod)
        assert pod.state == "Exited"


def test_create_hostname_arg(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name, hostname="myhost") as pod:
        output = podman_client.container.run(
            "ubuntu", ["cat", "/etc/hostname"], pod=pod
        )
        assert output == "myhost"


def test_create_infra_arg(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name, infra=False) as pod:
        podman_client.container.run(
            "ubuntu", ["sleep", "infinity"], pod=pod, detach=True, stop_timeout=0
        )
        assert pod.num_containers == 1


def test_create_labels_arg(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name, labels={"foo": "bar"}) as pod:
        assert pod.labels == {"foo": "bar"}


def test_create_no_hosts_arg(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name, no_hosts=True) as pod:
        output = podman_client.container.run("ubuntu", ["cat", "/etc/hosts"], pod=pod)
        assert output == ""


def test_create_pod_id_file_arg(podman_client: DockerClient, tmp_path: Path):
    pod_name = random_name()
    pod_id_file = tmp_path / "id"
    with podman_client.pod.create(pod_name, pod_id_file=pod_id_file) as pod:
        assert pod.id == pod_id_file.read_text().strip()


def test_create_replace_arg(podman_client: DockerClient):
    pod_name = random_name()
    pod1 = podman_client.pod.create(pod_name)
    pod1_id = pod1.id
    with podman_client.pod.create(pod_name, replace=True) as pod2:
        assert not pod1.exists()
        assert pod1_id != pod2.id


def test_create_share_arg(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name, share=[], infra=True) as pod:
        pod.start()  # start the infra container
        assert not pod.shared_namespaces
        output = podman_client.container.run(
            "ubuntu", ["readlink", "/proc/self"], pod=pod
        )
        assert output == "1"
    with podman_client.pod.create(pod_name, share=["pid", "ipc"]) as pod:
        pod.start()  # start the infra container (PID 1)
        assert set(pod.shared_namespaces) == {"pid", "ipc"}
        output = podman_client.container.run(
            "ubuntu", ["readlink", "/proc/self"], pod=pod
        )
        assert re.fullmatch(r"\d+", output) and output != "1"


def test_create_shm_size_arg(podman_client: DockerClient):
    # Should skip if podman version is below 4.2 (need to implement
    # DockerClient.version).
    pod_name = random_name()
    with podman_client.pod.create(pod_name, shm_size=1_024_000) as pod:
        output = podman_client.container.run("ubuntu", ["findmnt", "/dev/shm"], pod=pod)
        assert "size=1000k" in output


@pytest.mark.parametrize(
    "method",
    ["inspect", "kill", "logs", "remove", "restart", "start", "stop"],
)
def test_functions_nosuchpod(method: str, podman_client: DockerClient):
    with pytest.raises(NoSuchPod):
        getattr(podman_client.pod, method)("pod-that-does-not-exist")
