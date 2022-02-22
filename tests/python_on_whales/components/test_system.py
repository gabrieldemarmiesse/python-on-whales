import json
from datetime import date
from pathlib import Path

import pytest

from python_on_whales import docker
from python_on_whales.components.system.models import DockerEvent, SystemInfo
from python_on_whales.exceptions import DockerException
from python_on_whales.test_utils import get_all_jsons, random_name


def test_disk_free():
    docker.pull("busybox")
    docker.pull("busybox:1")
    docker_items_summary = docker.system.disk_free()
    assert docker_items_summary.images.total_count >= 1
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
    json_file = Path(__file__).parent / "jsons/events/0.json"
    events = json.loads(json_file.read_text())["events"]
    for event in events:
        parsed: DockerEvent = DockerEvent.parse_obj(event)
        assert parsed.time.date() == date(2020, 12, 28)


def test_prune_prunes_image():
    # TODO: Test dangling image
    for container in docker.container.list(filters={"ancestor": "busybox"}):
        docker.container.remove(container, force=True)
    image = docker.pull("busybox")
    assert image in docker.image.list()

    # image not pruned because not dangling
    docker.system.prune()
    assert image in docker.image.list()

    # image not pruned because it does not have dne label
    docker.system.prune(all=True, filters={"label": "dne", "until": "1000000h"})
    assert image in docker.image.list()

    # image pruned
    docker.system.prune(all=True)
    assert image not in docker.image.list()


def test_prune_prunes_container():
    stopped_container = docker.run("hello-world", remove=False, detach=True)
    running_container = docker.run(
        "ubuntu", ["sleep", "infinity"], remove=False, detach=True
    )

    assert stopped_container in docker.container.list(all=True)
    assert running_container in docker.container.list()

    docker.system.prune()

    assert stopped_container not in docker.container.list(all=True)
    assert running_container in docker.container.list()
    docker.container.remove(running_container, force=True)


def test_prune_prunes_network():
    network_name = random_name()
    my_net = docker.network.create(network_name)
    assert my_net in docker.network.list()
    docker.system.prune()
    assert my_net not in docker.network.list()


def test_prune_prunes_volumes():
    some_volume = docker.volume.create(driver="local")
    docker.run(
        "ubuntu",
        ["touch", "/dodo/dada"],
        volumes=[(some_volume, "/dodo")],
        remove=False,
    )
    assert some_volume in docker.volume.list()

    docker.system.prune()
    assert some_volume in docker.volume.list()

    docker.system.prune(volumes=True)
    assert some_volume not in docker.volume.list()


def test_prune_raises_exception_on_invalid_arguments():
    """
    The "until" filter is not supported with "--volumes"

    docker.system.prune should reflect that
    """
    with pytest.raises(DockerException):
        docker.system.prune(volumes=True, filters={"until": "1000000h"})
