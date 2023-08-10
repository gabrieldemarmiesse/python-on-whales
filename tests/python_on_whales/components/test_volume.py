import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from python_on_whales import docker
from python_on_whales.components.volume.models import VolumeInspectResult
from python_on_whales.exceptions import NoSuchVolume
from python_on_whales.test_utils import get_all_jsons


@pytest.mark.parametrize("json_file", get_all_jsons("volumes"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    a = VolumeInspectResult(**json.loads(json_as_txt))
    if json_file.name == "0.json":
        assert a.created_at == datetime(
            year=2020,
            month=8,
            day=27,
            hour=9,
            minute=39,
            second=50,
            tzinfo=timezone(timedelta(hours=2)),
        )
        assert a.mountpoint == Path(
            "/var/lib/docker/volumes/dodo_letsencrypt_config/_data"
        )
        assert a.options is None


def test_simple_volume():
    some_volume = docker.volume.create()
    assert some_volume.exists()
    assert some_volume.name in repr(docker.volume.list())
    assert some_volume.driver in repr(docker.volume.list())
    docker.volume.remove(some_volume)


def test_multiple_volumes():
    volumes = [docker.volume.create() for _ in range(3)]

    for v in volumes:
        assert v in docker.volume.list()

    docker.volume.remove(volumes)

    for v in volumes:
        assert v not in docker.volume.list()


def test_volume_drivers():
    some_volume = docker.volume.create(
        driver="local",
        options=dict(type="tmpfs", device="tmpfs", o="size=100m,uid=1000"),
    )
    docker.run(
        "busybox",
        ["touch", "/dodo/dada"],
        volumes=[(some_volume, "/dodo")],
        remove=True,
    )
    docker.volume.remove(some_volume)


def test_volume_labels():
    some_volume = docker.volume.create(labels=dict(dodo="dada"))

    assert some_volume.labels["dodo"] == "dada"
    docker.volume.remove(some_volume)


def test_list():
    volumes = [docker.volume.create() for _ in range(3)]

    all_volumes = docker.volume.list()
    for v in volumes:
        assert v in all_volumes


def test_copy_to_volume(tmp_path):
    some_volume = docker.volume.create()
    docker.run(
        "busybox",
        ["touch", "/volume/dodo.txt"],
        remove=True,
        volumes=[(some_volume, "/volume")],
    )

    docker.volume.copy((some_volume, "dodo.txt"), tmp_path)
    assert (tmp_path / "dodo.txt").exists()


def test_copy_to_volume_subdirectory(tmp_path):
    some_volume = docker.volume.create()
    docker.run(
        "busybox",
        [
            "sh",
            "-c",
            "mkdir -p /volume/subdir/subdir2 && touch /volume/subdir/subdir2/dodo.txt",
        ],
        remove=True,
        volumes=[(some_volume, "/volume")],
    )

    docker.volume.copy((some_volume, "subdir/subdir2"), tmp_path)
    assert (tmp_path / "subdir2/dodo.txt").exists()


def test_copy_to_and_from_volume(tmp_path):
    some_volume = docker.volume.create()

    text_file = tmp_path / "some_dir" / "dodo.txt"
    text_file.parent.mkdir(parents=True)
    text_file.write_text("Hello\nWorld!")
    docker.volume.copy(tmp_path, (some_volume, "subdir"))

    text_file.unlink()
    docker.volume.copy((some_volume, "subdir/"), tmp_path)

    assert (tmp_path / "subdir/some_dir/dodo.txt").read_text() == "Hello\nWorld!"


def test_volume_cp_from_in_dir(tmp_path):
    some_volume = docker.volume.create()
    docker.run(
        "busybox",
        ["touch", "/volume/dodo.txt"],
        remove=True,
        volumes=[(some_volume, "/volume")],
    )

    docker.volume.copy((some_volume, "."), tmp_path)
    assert (tmp_path / "dodo.txt").exists()


def test_volume_cp_to_in_dir(tmp_path):
    dodo = tmp_path / "dada" / "dodo.txt"
    dodo.parent.mkdir()
    dodo.touch()
    some_volume = docker.volume.create()
    docker.volume.copy(str(tmp_path) + "/.", (some_volume, ""))
    files = docker.run(
        "busybox",
        ["ls", "/volume/dada/"],
        remove=True,
        volumes=[(some_volume, "/volume")],
    )

    assert files == "dodo.txt"


def test_clone():
    some_volume = docker.volume.create()
    docker.run(
        "busybox",
        [
            "sh",
            "-c",
            "mkdir -p /volume/subdir/subdir2 && touch /volume/subdir/subdir2/dodo.txt",
        ],
        remove=True,
        volumes=[(some_volume, "/volume")],
    )

    new_volume = docker.volume.clone(some_volume)
    files = docker.run(
        "busybox",
        [
            "sh",
            "-c",
            "ls /volume/subdir/subdir2",
        ],
        remove=True,
        volumes=[(new_volume, "/volume")],
    )
    assert files == "dodo.txt"


@pytest.mark.parametrize(
    "docker_function", [docker.volume.inspect, docker.volume.remove]
)
def test_functions_no_such_volume(docker_function):
    with pytest.raises(NoSuchVolume) as e:
        docker_function("dodo")
    assert "no such volume" in str(e.value).lower()


def test_volume_does_not_exists():
    assert not docker.volume.exists("dodo")


def test_volume_exists():
    with docker.volume.create() as v:
        assert v.exists()
        assert docker.volume.exists(v.name)


def test_prune():
    for volume in docker.volume.list(filters={"name": "test-volume"}):
        volume.remove()
    volume = docker.volume.create("test-volume")
    assert volume in docker.volume.list()

    # volume not pruned because it does not have label "dne"
    docker.volume.prune(filters={"label": "dne"}, all=True)
    assert volume in docker.volume.list()

    # could only find "label" filter for `docker volume prune`

    # volume pruned
    docker.volume.prune(all=True)
    assert volume not in docker.volume.list()


def test_volume_remove_empty_list():
    with docker.volume.create() as my_volume:
        assert my_volume in docker.volume.list()
        all_volumes = set(docker.volume.list())
        docker.volume.remove([])
        assert all_volumes == set(docker.volume.list())
