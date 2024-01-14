import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from python_on_whales import DockerClient
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


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_volume(ctr_client: DockerClient):
    some_volume = ctr_client.volume.create()
    assert some_volume.exists()
    assert some_volume.name in repr(ctr_client.volume.list())
    assert some_volume.driver in repr(ctr_client.volume.list())
    ctr_client.volume.remove(some_volume)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_multiple_volumes(ctr_client: DockerClient):
    volumes = [ctr_client.volume.create() for _ in range(3)]

    for v in volumes:
        assert v in ctr_client.volume.list()

    ctr_client.volume.remove(volumes)

    for v in volumes:
        assert v not in ctr_client.volume.list()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_volume_drivers(ctr_client: DockerClient):
    some_volume = ctr_client.volume.create(
        driver="local",
        options=dict(type="tmpfs", device="tmpfs", o="size=100m,uid=1000"),
    )
    ctr_client.run(
        "busybox",
        ["touch", "/dodo/dada"],
        volumes=[(some_volume, "/dodo")],
        remove=True,
    )
    ctr_client.volume.remove(some_volume)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_volume_labels(ctr_client: DockerClient):
    some_volume = ctr_client.volume.create(labels=dict(dodo="dada"))

    assert some_volume.labels["dodo"] == "dada"
    ctr_client.volume.remove(some_volume)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_list(ctr_client: DockerClient):
    volumes = [ctr_client.volume.create() for _ in range(3)]

    all_volumes = ctr_client.volume.list()
    for v in volumes:
        assert v in all_volumes


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_copy_to_volume(ctr_client: DockerClient, tmp_path: Path):
    some_volume = ctr_client.volume.create()
    ctr_client.run(
        "busybox",
        ["touch", "/volume/dodo.txt"],
        remove=True,
        volumes=[(some_volume, "/volume")],
    )

    ctr_client.volume.copy((some_volume, "dodo.txt"), tmp_path)
    assert (tmp_path / "dodo.txt").exists()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_copy_to_volume_subdirectory(ctr_client: DockerClient, tmp_path: Path):
    some_volume = ctr_client.volume.create()
    ctr_client.run(
        "busybox",
        [
            "sh",
            "-c",
            "mkdir -p /volume/subdir/subdir2 && touch /volume/subdir/subdir2/dodo.txt",
        ],
        remove=True,
        volumes=[(some_volume, "/volume")],
    )

    ctr_client.volume.copy((some_volume, "subdir/subdir2"), tmp_path)
    assert (tmp_path / "subdir2/dodo.txt").exists()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_copy_to_and_from_volume(ctr_client: DockerClient, tmp_path: Path):
    some_volume = ctr_client.volume.create()

    text_file = tmp_path / "some_dir" / "dodo.txt"
    text_file.parent.mkdir(parents=True)
    text_file.write_text("Hello\nWorld!")
    ctr_client.volume.copy(tmp_path, (some_volume, "subdir"))

    text_file.unlink()
    ctr_client.volume.copy((some_volume, "subdir/"), tmp_path)

    assert (tmp_path / "subdir/some_dir/dodo.txt").read_text() == "Hello\nWorld!"


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_volume_cp_from_in_dir(ctr_client: DockerClient, tmp_path: Path):
    some_volume = ctr_client.volume.create()
    ctr_client.run(
        "busybox",
        ["touch", "/volume/dodo.txt"],
        remove=True,
        volumes=[(some_volume, "/volume")],
    )

    ctr_client.volume.copy((some_volume, "."), tmp_path)
    assert (tmp_path / "dodo.txt").exists()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_volume_cp_to_in_dir(ctr_client: DockerClient, tmp_path: Path):
    dodo = tmp_path / "dada" / "dodo.txt"
    dodo.parent.mkdir()
    dodo.touch()
    some_volume = ctr_client.volume.create()
    ctr_client.volume.copy(str(tmp_path) + "/.", (some_volume, ""))
    files = ctr_client.run(
        "busybox",
        ["ls", "/volume/dada/"],
        remove=True,
        volumes=[(some_volume, "/volume")],
    )

    assert files == "dodo.txt"


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_clone(ctr_client: DockerClient):
    some_volume = ctr_client.volume.create()
    ctr_client.run(
        "busybox",
        [
            "sh",
            "-c",
            "mkdir -p /volume/subdir/subdir2 && touch /volume/subdir/subdir2/dodo.txt",
        ],
        remove=True,
        volumes=[(some_volume, "/volume")],
    )

    new_volume = ctr_client.volume.clone(some_volume)
    files = ctr_client.run(
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


@pytest.mark.parametrize("method", ["inspect", "remove"])
@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_functions_no_such_volume(ctr_client: DockerClient, method: str):
    with pytest.raises(NoSuchVolume) as e:
        getattr(ctr_client.volume, method)("dodo")
    assert "no such volume" in str(e.value).lower()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_volume_does_not_exists(ctr_client: DockerClient):
    assert not ctr_client.volume.exists("dodo")


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_volume_exists(ctr_client: DockerClient):
    with ctr_client.volume.create() as v:
        assert v.exists()
        assert ctr_client.volume.exists(v.name)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_prune(ctr_client: DockerClient):
    for volume in ctr_client.volume.list(filters={"name": "test-volume"}):
        volume.remove()
    volume = ctr_client.volume.create("test-volume")
    assert volume in ctr_client.volume.list()

    # volume not pruned because it does not have label "dne"
    ctr_client.volume.prune(filters={"label": "dne"}, all=True)
    assert volume in ctr_client.volume.list()

    # could only find "label" filter for `docker volume prune`

    # volume pruned
    ctr_client.volume.prune(all=True)
    assert volume not in ctr_client.volume.list()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_volume_remove_empty_list(ctr_client: DockerClient):
    with ctr_client.volume.create() as my_volume:
        assert my_volume in ctr_client.volume.list()
        all_volumes = set(ctr_client.volume.list())
        ctr_client.volume.remove([])
        assert all_volumes == set(ctr_client.volume.list())
