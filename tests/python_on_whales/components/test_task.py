from pathlib import Path

import pytest

from python_on_whales import docker
from python_on_whales.components.task import TaskInspectResult


def get_all_tasks_jsons():
    jsons_directory = Path(__file__).parent / "tasks"
    return sorted(list(jsons_directory.iterdir()))


@pytest.mark.parametrize("json_file", get_all_tasks_jsons())
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    TaskInspectResult.parse_raw(json_as_txt)
    # we could do more checks here if needed


@pytest.mark.usefixtures("swarm_mode")
def test_list_tasks():
    service = docker.service.create("busybox", ["sleep", "infinity"])

    # Todo: use a context manager
    tasks = docker.task.list()
    assert len(tasks) >= 1
    assert tasks[0].desired_state == "running"
    assert tasks[0].service_id == service.id
    docker.service.remove(service)
