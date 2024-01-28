import json
import signal
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Union
from unittest.mock import Mock, patch

import pytest

import python_on_whales
from python_on_whales import DockerClient
from python_on_whales.components.pod.cli_wrapper import Pod
from python_on_whales.components.pod.models import PodInspectResult
from python_on_whales.exceptions import DockerException, NoSuchPod
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
