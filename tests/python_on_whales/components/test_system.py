import json
from datetime import date
from pathlib import Path

import pytest

from python_on_whales import docker
from python_on_whales.components.system import DockerEvent, SystemInfo
from python_on_whales.test_utils import get_all_jsons


def test_disk_free():
    docker.pull("busybox")
    docker.pull("busybox:1")
    docker_items_summary = docker.system.disk_free()
    assert docker_items_summary.images.active > 1
    assert docker_items_summary.images.size > 2000


def test_info():
    info = docker.system.info()
    assert "local" in info.plugins.volume


@pytest.mark.parametrize("json_file", get_all_jsons("system_info"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    SystemInfo.parse_raw(json_as_txt)
    # we could do more checks here if needed


def test_parsing_events():
    json_file = Path(__file__).parent / "events/0.json"
    events = json.loads(json_file.read_text())["events"]
    for event in events:
        parsed: DockerEvent = DockerEvent.parse_obj(event)
        assert parsed.time.date() == date(2020, 12, 28)
