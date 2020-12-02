from python_on_whales import docker


def test_disk_free():
    docker.pull("busybox")
    docker.pull("busybox:1")
    docker_items_summary = docker.system.disk_free()
    assert docker_items_summary.images.active > 1
    assert docker_items_summary.images.size > 2000


def test_info():
    docker.system.info()
    pass
