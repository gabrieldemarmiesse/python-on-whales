from pathlib import Path

import pytest

from python_on_whales import DockerException, docker
from python_on_whales.components.image import ImageInspectResult
from python_on_whales.test_utils import random_name


def get_all_images_jsons():
    jsons_directory = Path(__file__).parent / "images"
    return sorted(list(jsons_directory.iterdir()))


@pytest.mark.parametrize("json_file", get_all_images_jsons())
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ImageInspectResult.parse_raw(json_as_txt)
    # we could do more checks here if needed


def test_image_remove():
    docker.image.pull("busybox:1", quiet=True)
    docker.image.pull("busybox:1.32", quiet=True)
    docker.image.remove(["busybox:1", "busybox:1.32"])


def test_image_save_load(tmp_path):
    tar_file = tmp_path / "dodo.tar"
    docker.image.pull("busybox:1", quiet=True)
    docker.image.save("busybox:1", output=tar_file)
    docker.image.remove("busybox:1")
    assert docker.image.load(input=tar_file) == ["busybox:1"]


def test_save_iterator_bytes():
    docker.image.pull("busybox:1", quiet=True)
    iterator = docker.image.save("busybox:1")

    for i, my_bytes in enumerate(iterator):
        if i == 0:
            assert len(my_bytes) != 0

    assert i != 0


def test_save_iterator_bytes_fails():
    docker.image.pull("busybox:1", quiet=True)
    iterator = docker.image.save("busybox:42")

    with pytest.raises(DockerException) as err:
        for _ in iterator:
            pass
    assert "docker image save busybox:42" in str(err.value)
    assert "Error response from daemon: reference does not exist" in str(err.value)


def test_save_iterator_bytes_and_load():
    image_name = "busybox:1"
    docker.image.pull(image_name, quiet=True)
    iterator = docker.image.save(image_name)

    my_tar_as_bytes = b"".join(iterator)

    docker.image.remove(image_name)

    loaded = docker.image.load(my_tar_as_bytes)
    assert loaded == [image_name]
    docker.image.inspect(image_name)


def test_save_iterator_bytes_and_load_from_iterator():
    image_name = "busybox:1"
    docker.image.pull(image_name, quiet=True)
    iterator = docker.image.save(image_name)

    assert docker.image.load(iterator) == [image_name]
    docker.image.inspect(image_name)


def test_save_iterator_bytes_and_load_from_iterator_list_of_images():
    images = ["busybox:1", "hello-world:latest"]
    docker.image.pull(images[0], quiet=True)
    docker.image.pull(images[1], quiet=True)
    iterator = docker.image.save(images)

    assert set(docker.image.load(iterator)) == set(images)
    docker.image.inspect(images[0])
    docker.image.inspect(images[1])


def test_image_list():
    image_list = docker.image.list()
    all_ids = [x.id for x in image_list]
    all_ids_uniquified = set(all_ids)
    assert len(set(all_ids_uniquified)) == len(image_list)


def test_image_bulk_reload():
    pass


def test_image_list_tags():
    image_name = "busybox:1"
    docker.image.pull(image_name, quiet=True)
    all_images = docker.image.list()
    for image in all_images:
        if image_name in image.repo_tags:
            return
    else:
        raise ValueError("Tag not found in images.")


def test_pull_not_quiet():
    try:
        docker.image.remove("busybox:1")
    except DockerException:
        pass
    image = docker.image.pull("busybox:1")
    assert "busybox:1" in image.repo_tags


def test_copy_from_and_to(tmp_path):
    my_image = docker.pull("busybox:1")
    (tmp_path / "dodo.txt").write_text("Hello world!")

    new_image_name = random_name()
    my_image.copy_to(tmp_path / "dodo.txt", "/dada.txt", new_tag=new_image_name)

    new_image_name = docker.image.inspect(new_image_name)
    new_image_name.copy_from("/dada.txt", tmp_path / "dudu.txt")
    assert (tmp_path / "dodo.txt").read_text() == (tmp_path / "dudu.txt").read_text()


def test_copy_from_and_to_directory(tmp_path):
    my_image = docker.pull("busybox:1")
    (tmp_path / "dodo.txt").write_text("Hello world!")

    new_image_name = random_name()
    my_image.copy_to(tmp_path, "/some_path", new_tag=new_image_name)

    new_image_name = docker.image.inspect(new_image_name)
    new_image_name.copy_from("/some_path", tmp_path / "some_path")
    assert "Hello world!" == (tmp_path / "some_path" / "dodo.txt").read_text()


def test_many_images():
    # TODO: get the json inspects results and put them in the "images/" directory
    for tag in [
        "ubuntu:16.04",
        "ubuntu:18.04",
        "ubuntu:20.04",
        "busybox:1",
        "traefik:v2.3.2",
        "redis:alpine3.12",
        "docker:19.03.13",
    ]:
        docker.pull(tag)._get_inspect_result()
