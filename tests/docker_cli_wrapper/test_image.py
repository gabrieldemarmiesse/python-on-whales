from docker_cli_wrapper import docker


def test_image_remove():
    docker.image.pull("busybox:1", quiet=True)
    docker.image.pull("busybox:1.32", quiet=True)
    docker.image.remove(["busybox:1", "busybox:1.32"])
