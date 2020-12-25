from pathlib import Path
from typing import List

import pytest

from python_on_whales import docker
from python_on_whales.components.system import SystemInfoResults


def test_disk_free():
    docker.pull("busybox")
    docker.pull("busybox:1")
    docker_items_summary = docker.system.disk_free()
    assert docker_items_summary.images.active > 1
    assert docker_items_summary.images.size > 2000


def test_info():
    docker.system.info()
    pass


def get_all_system_info_jsons() -> List[Path]:
    jsons_directory = Path(__file__).parent / "system_info"
    return sorted(list(jsons_directory.iterdir()))


@pytest.mark.parametrize("json_file", get_all_system_info_jsons())
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    SystemInfoResults.parse_raw(json_as_txt)
    # we could do more checks here if needed
