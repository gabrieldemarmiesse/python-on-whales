from datetime import datetime, timedelta, timezone
from pathlib import Path

from docker_cli_wrapper import docker
from docker_cli_wrapper.components.volume import VolumeInspectResult


def test_simple_volume():
    some_volume = docker.volume.create()
    docker.volume.remove(some_volume)


def test_multiple_volumes():
    volumes = [docker.volume.create() for _ in range(3)]

    volumes_deleted = docker.volume.remove(volumes)
    assert volumes_deleted == [x.name for x in volumes]


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

    assert some_volume.labels == dict(dodo="dada")
    docker.volume.remove(some_volume)


def test_list():
    volumes = [docker.volume.create() for _ in range(3)]

    all_volumes = docker.volume.list()
    for v in volumes:
        assert v in all_volumes


json_volume_inspect = """
{
    "CreatedAt": "2020-08-27T09:39:50+02:00",
    "Driver": "local",
    "Labels": {
        "com.docker.compose.project": "some_project",
        "com.docker.compose.version": "1.25.5",
        "com.docker.compose.volume": "letsencrypt_config"
    },
    "Mountpoint": "/var/lib/docker/volumes/scube_letsencrypt_config/_data",
    "Name": "scube_letsencrypt_config",
    "Options": null,
    "Scope": "local"
}
"""


def test_volume_inspect_result_config():

    a = VolumeInspectResult.parse_raw(json_volume_inspect)
    assert a.CreatedAt == datetime(
        year=2020,
        month=8,
        day=27,
        hour=9,
        minute=39,
        second=50,
        tzinfo=timezone(timedelta(hours=2)),
    )
    assert a.Mountpoint == Path(
        "/var/lib/docker/volumes/scube_letsencrypt_config/_data"
    )
    assert a.Options is None
