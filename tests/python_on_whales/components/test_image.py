import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from python_on_whales import docker
from python_on_whales.components.image.models import ImageInspectResult
from python_on_whales.exceptions import DockerException, NoSuchImage
from python_on_whales.test_utils import get_all_jsons, random_name


@pytest.mark.parametrize("json_file", get_all_jsons("images"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ImageInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


def test_image_repr():
    docker.image.pull("busybox:1", quiet=True)
    docker.image.pull("busybox:1.32", quiet=True)
    assert "busybox:1" in repr(docker.image.list())
    assert "busybox:1.32" in repr(docker.image.list())
    docker.image.remove(["busybox:1", "busybox:1.32"])


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


def test_filter_when_listing():
    docker.pull(["hello-world", "busybox"])
    images_listed = docker.image.list(filters=dict(reference="hello-world"))
    tags = set()
    for image in images_listed:
        for tag in image.repo_tags:
            tags.add(tag)
    assert tags == {"hello-world:latest"}


def test_filter_when_listing_old_signature():
    """Check backward compatibility"""
    docker.pull(["hello-world", "busybox"])
    with pytest.warns(DeprecationWarning) as warnings_emmitted:
        images_listed = docker.image.list({"reference": "hello-world"})

    warning_message = str(warnings_emmitted.list[0].message)
    assert "docker.image.list({'reference': 'hello-world'}" in warning_message
    assert "docker.image.list(filters={'reference': 'hello-world'}" in warning_message
    tags = set()
    for image in images_listed:
        for tag in image.repo_tags:
            tags.add(tag)
    assert tags == {"hello-world:latest"}


def test_use_first_argument_to_filter():
    """Check backward compatibility"""
    docker.pull(["hello-world", "busybox"])
    images_listed = docker.image.list("hello-world")
    tags = set()
    for image in images_listed:
        for tag in image.repo_tags:
            tags.add(tag)
    assert tags == {"hello-world:latest"}


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


def test_pull_not_quiet_multiple_images():
    images_names = ["busybox:1", "hello-world:latest"]
    try:
        docker.image.remove(images_names)
    except DockerException:
        pass
    images = docker.pull(images_names)
    for image_name, image in zip(images_names, images):
        assert image_name in image.repo_tags


def test_pull_not_quiet_multiple_images_break():
    images_names = ["busybox:1", "hellstuff"]
    try:
        docker.image.remove(images_names)
    except DockerException:
        pass

    with pytest.raises(DockerException) as err:
        docker.pull(images_names)

    assert "docker image pull hellstuff" in str(err.value)


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


def test_prune():
    docker.pull("busybox")
    docker.image.prune(all=True)
    with pytest.raises(DockerException):
        docker.image.inspect("busybox")


def test_remove_nothing():
    with docker.pull("hello-world"):
        all_images = set(docker.image.list())
        docker.image.remove([])
        assert all_images == set(docker.image.list())


@pytest.mark.parametrize(
    "docker_function", [docker.image.inspect, docker.image.remove, docker.push]
)
def test_no_such_image_with_multiple_functions(docker_function):
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        docker_function(image_name_that_does_not_exists)

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


def test_no_such_image_save():
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        docker.image.save(image_name_that_does_not_exists, output="/tmp/dada")

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


def test_no_such_image_save_generator():
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        for _ in docker.image.save(image_name_that_does_not_exists):
            pass

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


def test_no_such_image_tag():
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        docker.image.tag(image_name_that_does_not_exists, "something")

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


def test_exists():
    my_image = docker.pull("busybox")
    assert my_image.exists()
    assert docker.image.exists("busybox")

    assert not docker.image.exists("dudurghurozgiozpfezjigfoeioengizeonig")


@patch("python_on_whales.components.image.cli_wrapper.ContainerCLI")
def test_copy_from_default_pull(container_mock: Mock) -> None:
    container_cli_mock = MagicMock()
    container_mock.return_value = container_cli_mock

    test_image_name = "test_dummy_image"

    docker.image.copy_from(
        test_image_name, "test_path_in_image", "test_local_destination"
    )

    container_cli_mock.create.assert_called_with(test_image_name, pull="missing")


@patch("python_on_whales.components.image.cli_wrapper.ContainerCLI")
def test_copy_from_pull(container_mock: Mock) -> None:
    container_cli_mock = MagicMock()
    container_mock.return_value = container_cli_mock

    test_image_name = "test_dummy_image"
    test_pull_flag = "test_pull_flag_value"

    docker.image.copy_from(
        test_image_name,
        "test_path_in_image",
        "test_local_destination",
        pull=test_pull_flag,
    )

    container_cli_mock.create.assert_called_with(test_image_name, pull=test_pull_flag)


@patch("python_on_whales.components.image.cli_wrapper.ContainerCLI")
def test_copy_to_default_pull(container_mock: Mock) -> None:
    container_cli_mock = MagicMock()
    container_mock.return_value = container_cli_mock

    test_image_name = "test_dummy_image"

    docker.image.copy_to(
        test_image_name, "test_local_destination", "test_path_in_image"
    )

    container_cli_mock.create.assert_called_with(test_image_name, pull="missing")


@patch("python_on_whales.components.image.cli_wrapper.ContainerCLI")
def test_copy_to_pull(container_mock: Mock) -> None:
    container_cli_mock = MagicMock()
    container_mock.return_value = container_cli_mock

    test_image_name = "test_dummy_image"
    test_pull_flag = "test_pull_flag_value"

    docker.image.copy_to(
        test_image_name,
        "test_local_destination",
        "test_path_in_image",
        pull=test_pull_flag,
    )

    container_cli_mock.create.assert_called_with(test_image_name, pull=test_pull_flag)
