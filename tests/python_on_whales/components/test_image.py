import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from python_on_whales import DockerClient, docker
from python_on_whales.components.image.models import ImageInspectResult
from python_on_whales.exceptions import DockerException, NoSuchImage
from python_on_whales.test_utils import (
    get_all_jsons,
    parametrize_ctr_client,
    random_name,
)


@pytest.mark.parametrize("json_file", get_all_jsons("images"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ImageInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


@parametrize_ctr_client("docker", "podman")
def test_image_repr(ctr_client: DockerClient):
    ctr_client.image.pull("busybox:1", quiet=True)
    ctr_client.image.pull("busybox:1.32", quiet=True)
    assert "busybox:1" in repr(ctr_client.image.list())
    assert "busybox:1.32" in repr(ctr_client.image.list())
    ctr_client.image.remove(["busybox:1", "busybox:1.32"])


@parametrize_ctr_client("docker", "podman")
def test_image_remove(ctr_client: DockerClient):
    ctr_client.image.pull("busybox:1", quiet=True)
    ctr_client.image.pull("busybox:1.32", quiet=True)
    ctr_client.image.remove(["busybox:1", "busybox:1.32"])


@parametrize_ctr_client("docker", "podman")
def test_image_save_load(ctr_client: DockerClient, tmp_path: Path):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    tar_file = tmp_path / "dodo.tar"
    ctr_client.image.pull("busybox:1", quiet=True)
    ctr_client.image.save("busybox:1", output=tar_file)
    ctr_client.image.remove("busybox:1")
    assert ctr_client.image.load(input=tar_file) == ["busybox:1"]


@parametrize_ctr_client("docker", "podman")
def test_save_iterator_bytes(ctr_client: DockerClient):
    ctr_client.image.pull("busybox:1", quiet=True)
    iterator = ctr_client.image.save("busybox:1")

    for i, my_bytes in enumerate(iterator):
        if i == 0:
            assert len(my_bytes) != 0

    assert i != 0


@parametrize_ctr_client("docker", "podman")
def test_filter_when_listing(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    ctr_client.pull(["hello-world", "busybox"])
    images_listed = ctr_client.image.list(filters=dict(reference="hello-world"))
    tags = set()
    for image in images_listed:
        for tag in image.repo_tags:
            tags.add(tag)
    assert tags == {"hello-world:latest"}


def test_filter_when_listing_old_signature(docker_client: DockerClient):
    """Check backward compatibility of the DockerClient.image.list() API."""
    docker_client.pull(["hello-world", "busybox"])
    with pytest.warns(DeprecationWarning) as warnings_emmitted:
        images_listed = docker_client.image.list({"reference": "hello-world"})

    warning_message = str(warnings_emmitted.list[0].message)
    assert "docker.image.list({'reference': 'hello-world'}" in warning_message
    assert "docker.image.list(filters={'reference': 'hello-world'}" in warning_message
    tags = set()
    for image in images_listed:
        for tag in image.repo_tags:
            tags.add(tag)
    assert tags == {"hello-world:latest"}


@parametrize_ctr_client("docker", "podman")
def test_use_first_argument_to_filter(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    ctr_client.pull(["hello-world", "busybox"])
    images_listed = ctr_client.image.list("hello-world")
    tags = set()
    for image in images_listed:
        for tag in image.repo_tags:
            tags.add(tag)
    assert tags == {"hello-world:latest"}


@parametrize_ctr_client("docker", "podman")
def test_save_iterator_bytes_and_load(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    image_name = "busybox:1"
    ctr_client.image.pull(image_name, quiet=True)
    iterator = ctr_client.image.save(image_name)

    my_tar_as_bytes = b"".join(iterator)

    ctr_client.image.remove(image_name)

    loaded = ctr_client.image.load(my_tar_as_bytes)
    assert loaded == [image_name]
    ctr_client.image.inspect(image_name)


@parametrize_ctr_client("docker", "podman")
def test_save_iterator_bytes_and_load_from_iterator(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    image_name = "busybox:1"
    ctr_client.image.pull(image_name, quiet=True)
    iterator = ctr_client.image.save(image_name)

    assert ctr_client.image.load(iterator) == [image_name]
    ctr_client.image.inspect(image_name)


@parametrize_ctr_client("docker", "podman")
def test_save_iterator_bytes_and_load_from_iterator_list_of_images(
    ctr_client: DockerClient,
):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    images = ["busybox:1", "hello-world:latest"]
    ctr_client.image.pull(images[0], quiet=True)
    ctr_client.image.pull(images[1], quiet=True)
    iterator = ctr_client.image.save(images)

    assert set(ctr_client.image.load(iterator)) == set(images)
    ctr_client.image.inspect(images[0])
    ctr_client.image.inspect(images[1])


@parametrize_ctr_client("docker", "podman")
def test_image_list(ctr_client: DockerClient):
    image_list = ctr_client.image.list()
    all_ids = [x.id for x in image_list]
    all_ids_uniquified = set(all_ids)
    assert len(set(all_ids_uniquified)) == len(image_list)


@parametrize_ctr_client("docker", "podman")
def test_image_bulk_reload(ctr_client: DockerClient):
    pass


@parametrize_ctr_client("docker", "podman")
def test_image_list_tags(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    image_name = "busybox:1"
    ctr_client.image.pull(image_name, quiet=True)
    all_images = ctr_client.image.list()
    for image in all_images:
        if image_name in image.repo_tags:
            return
    else:
        raise ValueError("Tag not found in images.")


@parametrize_ctr_client("docker", "podman")
def test_pull_not_quiet(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    try:
        ctr_client.image.remove("busybox:1")
    except DockerException:
        pass
    image = ctr_client.image.pull("busybox:1")
    assert "busybox:1" in image.repo_tags


@parametrize_ctr_client("docker", "podman")
def test_pull_not_quiet_multiple_images(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    images_names = ["busybox:1", "hello-world:latest"]
    try:
        ctr_client.image.remove(images_names)
    except DockerException:
        pass
    images = ctr_client.pull(images_names)
    for image_name, image in zip(images_names, images):
        assert image_name in image.repo_tags


@parametrize_ctr_client("docker", "podman")
def test_pull_not_quiet_multiple_images_break(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    images_names = ["busybox:1", "hellstuff"]
    try:
        ctr_client.image.remove(images_names)
    except DockerException:
        pass

    with pytest.raises(DockerException) as err:
        ctr_client.pull(images_names)

    assert "docker image pull hellstuff" in str(err.value)


@parametrize_ctr_client("docker", "podman")
def test_copy_from_and_to(ctr_client: DockerClient, tmp_path: Path):
    my_image = ctr_client.pull("busybox:1")
    (tmp_path / "dodo.txt").write_text("Hello world!")

    new_image_name = random_name()
    my_image.copy_to(tmp_path / "dodo.txt", "/dada.txt", new_tag=new_image_name)

    new_image_name = ctr_client.image.inspect(new_image_name)
    new_image_name.copy_from("/dada.txt", tmp_path / "dudu.txt")
    assert (tmp_path / "dodo.txt").read_text() == (tmp_path / "dudu.txt").read_text()


@parametrize_ctr_client("docker", "podman")
def test_copy_from_and_to_directory(ctr_client: DockerClient, tmp_path: Path):
    my_image = ctr_client.pull("busybox:1")
    (tmp_path / "dodo.txt").write_text("Hello world!")

    new_image_name = random_name()
    my_image.copy_to(tmp_path, "/some_path", new_tag=new_image_name)

    new_image_name = ctr_client.image.inspect(new_image_name)
    new_image_name.copy_from("/some_path", tmp_path / "some_path")
    assert "Hello world!" == (tmp_path / "some_path" / "dodo.txt").read_text()


@parametrize_ctr_client("docker", "podman")
def test_prune(ctr_client: DockerClient):
    ctr_client.pull("busybox")
    ctr_client.image.prune(all=True)
    with pytest.raises(DockerException):
        ctr_client.image.inspect("busybox")


@parametrize_ctr_client("docker", "podman")
def test_remove_nothing(ctr_client: DockerClient):
    with ctr_client.pull("hello-world"):
        all_images = set(ctr_client.image.list())
        ctr_client.image.remove([])
        assert all_images == set(ctr_client.image.list())


@parametrize_ctr_client("docker", "podman")
def test_no_such_image_inspect(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.image.inspect(image_name_that_does_not_exists)

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@parametrize_ctr_client("docker", "podman")
def test_no_such_image_remove(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.image.remove(image_name_that_does_not_exists)

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@parametrize_ctr_client("docker", "podman")
def test_no_such_image_push(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.push(image_name_that_does_not_exists)

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@parametrize_ctr_client("docker", "podman")
def test_no_such_image_save(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.image.save(image_name_that_does_not_exists, output="/tmp/dada")

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@parametrize_ctr_client("docker", "podman")
def test_no_such_image_save_generator(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        for _ in ctr_client.image.save(image_name_that_does_not_exists):
            pass

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@parametrize_ctr_client("docker", "podman")
def test_no_such_image_tag(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.image.tag(image_name_that_does_not_exists, "something")

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@parametrize_ctr_client("docker", "podman")
def test_exists(ctr_client: DockerClient):
    if ctr_client.client_config.client_type == "podman":
        pytest.xfail()
    my_image = ctr_client.pull("busybox")
    assert my_image.exists()
    assert ctr_client.image.exists("busybox")

    assert not ctr_client.image.exists("dudurghurozgiozpfezjigfoeioengizeonig")


@patch("python_on_whales.components.image.cli_wrapper.ContainerCLI")
def test_copy_from_default_pull(container_mock: Mock):
    container_cli_mock = MagicMock()
    container_mock.return_value = container_cli_mock

    test_image_name = "test_dummy_image"

    docker.image.copy_from(
        test_image_name, "test_path_in_image", "test_local_destination"
    )

    container_cli_mock.create.assert_called_with(test_image_name, pull="missing")


@patch("python_on_whales.components.image.cli_wrapper.ContainerCLI")
def test_copy_from_pull(container_mock: Mock):
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
def test_copy_to_default_pull(container_mock: Mock):
    container_cli_mock = MagicMock()
    container_mock.return_value = container_cli_mock

    test_image_name = "test_dummy_image"

    docker.image.copy_to(
        test_image_name, "test_local_destination", "test_path_in_image"
    )

    container_cli_mock.create.assert_called_with(test_image_name, pull="missing")


@patch("python_on_whales.components.image.cli_wrapper.ContainerCLI")
def test_copy_to_pull(container_mock: Mock):
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
