from docker_cli_wrapper import docker


def test_simple_volume():
    some_volume = docker.volume.create()
    docker.volume.remove(some_volume)


def test_multiple_volumes():
    volumes = [docker.volume.create() for _ in range(3)]

    volumes_deleted = docker.volume.remove(volumes)
    assert volumes_deleted == volumes
