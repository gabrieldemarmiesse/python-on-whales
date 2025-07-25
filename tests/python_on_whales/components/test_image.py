import contextlib
import json
from pathlib import Path
from typing import Generator
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest

from python_on_whales import DockerClient, docker
from python_on_whales.components.image.models import ImageInspectResult
from python_on_whales.exceptions import DockerException, NoSuchImage
from python_on_whales.test_utils import get_all_jsons, random_name


@pytest.mark.parametrize("json_file", get_all_jsons("images"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ImageInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_image_repr(ctr_client: DockerClient):
    ctr_client.image.pull("busybox:1", quiet=True)
    ctr_client.image.pull("busybox:1.32", quiet=True)
    assert "busybox:1" in repr(ctr_client.image.list())
    assert "busybox:1.32" in repr(ctr_client.image.list())
    ctr_client.image.remove(["busybox:1", "busybox:1.32"])


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_image_remove(ctr_client: DockerClient):
    ctr_client.image.pull("busybox:1", quiet=True)
    ctr_client.image.pull("busybox:1.32", quiet=True)
    ctr_client.image.remove(["busybox:1", "busybox:1.32"])


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_save_load(ctr_client: DockerClient, tmp_path: Path):
    tar_file = tmp_path / "dodo.tar"
    image_name = "busybox:1"
    image = ctr_client.image.pull(image_name, quiet=True)
    image_tag = [tag for tag in image.repo_tags if tag.endswith(image_name)][0]
    ctr_client.image.save(image_name, output=tar_file)
    ctr_client.image.remove(image_name, force=True)
    assert not ctr_client.image.exists(image_name)
    loaded_tags = ctr_client.image.load(input=tar_file)
    assert loaded_tags == [image_tag]
    assert ctr_client.image.exists(image_name)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_save_iterator_bytes(ctr_client: DockerClient):
    ctr_client.image.pull("busybox:1", quiet=True)
    iterator = ctr_client.image.save("busybox:1")

    for i, my_bytes in enumerate(iterator):
        if i == 0:
            assert len(my_bytes) != 0

    assert i != 0


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_save_iterator_bytes_and_load(ctr_client: DockerClient):
    image_name = "busybox:1"
    image = ctr_client.image.pull(image_name, quiet=True)
    image_tag = [tag for tag in image.repo_tags if tag.endswith(image_name)][0]
    iterator = ctr_client.image.save(image_name)
    my_tar_as_bytes = b"".join(iterator)
    image.remove(force=True)
    assert ctr_client.image.load(my_tar_as_bytes) == [image_tag]
    assert ctr_client.image.exists(image_name)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_save_iterator_bytes_and_load_from_iterator(ctr_client: DockerClient):
    image_name = "busybox:1"
    image = ctr_client.image.pull(image_name, quiet=True)
    image_tag = [tag for tag in image.repo_tags if tag.endswith(image_name)][0]
    iterator = ctr_client.image.save(image_name)
    # Cannot remove the image here because the save may still be in progress!
    assert ctr_client.image.load(iterator) == [image_tag]


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_save_iterator_bytes_and_load_from_iterator_list_of_images(
    ctr_client: DockerClient,
):
    image_names = ["busybox:1", "hello-world:latest"]
    images = ctr_client.image.pull(image_names, quiet=True)
    image_tags = [
        tag
        for image in images
        for tag in image.repo_tags
        if any(tag.endswith(n) for n in image_names)
    ]
    iterator = ctr_client.image.save(image_names)
    # Cannot remove the image here because the save may still be in progress!
    assert set(ctr_client.image.load(iterator)) == set(image_tags)


@pytest.mark.parametrize(
    "ctr_client",
    [
        "docker",
        pytest.param(
            "podman",
            marks=pytest.mark.xfail(
                reason="podman includes all repo tags matching images ref"
            ),
        ),
    ],
    indirect=True,
)
def test_list_filters(ctr_client: DockerClient):
    ctr_client.pull(["hello-world", "busybox"])
    images_listed = ctr_client.image.list(filters=[("reference", "hello-world")])
    tags = {tag.split("/")[-1] for image in images_listed for tag in image.repo_tags}
    assert tags == {"hello-world:latest"}


def test_list_filters_old_signature(docker_client: DockerClient):
    """Check backward compatibility of the DockerClient.image.list() API."""
    docker_client.pull(["hello-world", "busybox"])
    expected_warning = (
        r"Passing filters as a mapping is deprecated, replace with an iterable "
        r"of tuples instead, as so:\n"
        r"filters=\[\(.*\)\]"
    )
    with pytest.warns(DeprecationWarning, match=expected_warning):
        images_listed = docker_client.image.list(filters={"reference": "hello-world"})
    tags = {tag.split("/")[-1] for image in images_listed for tag in image.repo_tags}
    assert tags == {"hello-world:latest"}


@pytest.mark.parametrize(
    "ctr_client",
    [
        "docker",
        pytest.param(
            "podman",
            marks=pytest.mark.xfail(
                reason="podman includes all repo tags matching images ref"
            ),
        ),
    ],
    indirect=True,
)
def test_list_filter_by_name(ctr_client: DockerClient):
    ctr_client.pull(["hello-world", "busybox"])
    images_listed = ctr_client.image.list("hello-world")
    tags = {tag.split("/")[-1] for image in images_listed for tag in image.repo_tags}
    assert tags == {"hello-world:latest"}


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_image_list(ctr_client: DockerClient):
    image_list = ctr_client.image.list()
    all_ids = [x.id for x in image_list]
    all_ids_uniquified = set(all_ids)
    assert len(set(all_ids_uniquified)) == len(image_list)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_image_list_tags(ctr_client: DockerClient):
    ctr_client.image.pull("busybox:1", quiet=True)
    all_images = ctr_client.image.list()
    assert "busybox:1" in {
        tag.split("/")[-1] for image in all_images for tag in image.repo_tags
    }


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_pull_validation_error(ctr_client: DockerClient):
    with pytest.raises(ValueError) as err:
        ctr_client.image.pull(ANY, quiet=True, stream_logs=True)
    assert (
        "It's not possible to have stream_logs=True and quiet=True at the same time"
        in str(err.value)
    )


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_pull_nothing(ctr_client: DockerClient):
    result = ctr_client.image.pull([], quiet=True)
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_pull_nothing_stream_logs(ctr_client: DockerClient):
    result = ctr_client.image.pull([], stream_logs=True)
    assert isinstance(result, Generator)
    assert len(list(result)) == 0


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_pull_duplicate_images(ctr_client: DockerClient):
    with contextlib.suppress(DockerException):
        ctr_client.image.remove("busybox:1", force=True)
    images = ["busybox:1", "busybox:1", "busybox:1"]
    with patch(
        "python_on_whales.components.image.cli_wrapper.Image"
    ) as image, patch.object(
        ctr_client.image, "_pull_single_tag"
    ) as pull_single_tag, patch.object(
        ctr_client.image, "_pull_multiple_tags"
    ) as pull_multiple_tags:
        image.return_value = MagicMock()
        pull_single_tag.return_value = None
        ctr_client.image.pull(images, quiet=True)
        pull_multiple_tags.assert_not_called()
        pull_single_tag.assert_called_once()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_pull_not_quiet(ctr_client: DockerClient):
    with contextlib.suppress(DockerException):
        ctr_client.image.remove("busybox:1", force=True)
    image = ctr_client.image.pull("busybox:1")
    assert "busybox:1" in {tag.split("/")[-1] for tag in image.repo_tags}


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_pull_stream_logs(ctr_client: DockerClient):
    with contextlib.suppress(DockerException):
        ctr_client.image.remove("busybox:1", force=True)
    logs = ctr_client.image.pull("busybox:1", stream_logs=True)
    lines = [line.decode().strip() for _, line in logs]
    assert len(lines) > 0
    assert any("busybox:1" in line for line in lines)


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_pull_not_quiet_multiple_images(ctr_client: DockerClient):
    images_names = ["busybox:1", "hello-world:latest"]
    with contextlib.suppress(DockerException):
        ctr_client.image.remove(images_names, force=True)
    images = ctr_client.pull(images_names)
    for image_name, image in zip(images_names, images):
        assert image_name in image.repo_tags


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_pull_not_quiet_multiple_images_break(ctr_client: DockerClient):
    images_names = ["busybox:1", "hellstuff"]
    with contextlib.suppress(DockerException):
        ctr_client.image.remove(images_names, force=True)

    with pytest.raises(DockerException) as err:
        ctr_client.pull(images_names)
    assert f"{ctr_client.client_config.client_call[0]} image pull hellstuff" in str(
        err.value
    )


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_pull_stream_logs_multiple_images_break(ctr_client: DockerClient):
    images_names = ["busybox:1", "hellstuff"]
    with contextlib.suppress(DockerException):
        ctr_client.image.remove(images_names, force=True)

    with pytest.raises(DockerException) as err:
        logs = ctr_client.pull(images_names, stream_logs=True)
        for _ in logs:
            pass
    assert f"{ctr_client.client_config.client_call[0]} image pull hellstuff" in str(
        err.value
    )


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_push_validation_error(ctr_client: DockerClient):
    with pytest.raises(ValueError) as err:
        ctr_client.push(ANY, quiet=True, stream_logs=True)
    assert (
        "It's not possible to have stream_logs=True and quiet=True at the same time"
        in str(err.value)
    )


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_push_nothing(ctr_client: DockerClient):
    result = ctr_client.push([], quiet=True)
    assert result is None


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_push_nothing_stream_logs(ctr_client: DockerClient):
    result = ctr_client.push([], stream_logs=True)
    assert result is None


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_push_duplicate_images(ctr_client: DockerClient):
    with contextlib.suppress(DockerException):
        ctr_client.image.remove("busybox:1", force=True)
    images = ["busybox:1", "busybox:1", "busybox:1"]
    with patch(
        "python_on_whales.components.image.cli_wrapper.Image"
    ) as image, patch.object(
        ctr_client.image, "_push_single_tag"
    ) as push_single_tag, patch.object(
        ctr_client.image, "_push_multiple_tags"
    ) as push_multiple_tags:
        image.return_value = MagicMock()
        push_single_tag.return_value = None
        ctr_client.image.push(images, quiet=True)
        push_multiple_tags.assert_not_called()
        push_single_tag.assert_called_once()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_push_not_quiet_multiple_images_break(ctr_client: DockerClient):
    with contextlib.suppress(DockerException):
        ctr_client.image.remove("busybox:1", force=True)
    ctr_client.image.pull("busybox:1", quiet=True)
    with pytest.raises(NoSuchImage):
        ctr_client.push(["busybox:1", "hellstuff"])


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_push_stream_logs_multiple_images_break(ctr_client: DockerClient):
    with contextlib.suppress(DockerException):
        ctr_client.image.remove("busybox:1", force=True)
    ctr_client.image.pull("busybox:1", quiet=True)
    with pytest.raises(NoSuchImage):
        logs = ctr_client.push(["busybox:1", "hellstuff"])
        for _ in logs:
            pass


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_copy_from_and_to(ctr_client: DockerClient, tmp_path: Path):
    my_image = ctr_client.pull("busybox:1")
    (tmp_path / "dodo.txt").write_text("Hello world!")

    new_image_name = random_name()
    my_image.copy_to(tmp_path / "dodo.txt", "/dada.txt", new_tag=new_image_name)

    new_image_name = ctr_client.image.inspect(new_image_name)
    new_image_name.copy_from("/dada.txt", tmp_path / "dudu.txt")
    assert (tmp_path / "dodo.txt").read_text() == (tmp_path / "dudu.txt").read_text()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_copy_from_and_to_directory(ctr_client: DockerClient, tmp_path: Path):
    my_image = ctr_client.pull("busybox:1")
    (tmp_path / "dodo.txt").write_text("Hello world!")

    new_image_name = random_name()
    my_image.copy_to(tmp_path, "/some_path", new_tag=new_image_name)

    new_image_name = ctr_client.image.inspect(new_image_name)
    new_image_name.copy_from("/some_path", tmp_path / "some_path")
    assert "Hello world!" == (tmp_path / "some_path" / "dodo.txt").read_text()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_prune(ctr_client: DockerClient):
    ctr_client.pull("busybox")
    ctr_client.image.prune(all=True)
    with pytest.raises(DockerException):
        ctr_client.image.inspect("busybox")


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_remove_nothing(ctr_client: DockerClient):
    with ctr_client.pull("hello-world"):
        all_images = set(ctr_client.image.list())
        ctr_client.image.remove([])
        assert all_images == set(ctr_client.image.list())


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_no_such_image_inspect(ctr_client: DockerClient):
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.image.inspect(image_name_that_does_not_exists)

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_no_such_image_remove(ctr_client: DockerClient):
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.image.remove(image_name_that_does_not_exists)

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_no_such_image_push(ctr_client: DockerClient):
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.push(image_name_that_does_not_exists)

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_no_such_image_push_stream_logs(ctr_client: DockerClient):
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.push(image_name_that_does_not_exists, stream_logs=True)

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_no_such_image_save(ctr_client: DockerClient):
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.image.save(image_name_that_does_not_exists, output="/tmp/dada")

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_no_such_image_save_generator(ctr_client: DockerClient):
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        for _ in ctr_client.image.save(image_name_that_does_not_exists):
            pass

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_no_such_image_tag(ctr_client: DockerClient):
    image_name_that_does_not_exists = "dueizhguizhfezaezagrthyh"
    with pytest.raises(NoSuchImage) as err:
        ctr_client.image.tag(image_name_that_does_not_exists, "something")

    assert f"No such image: {image_name_that_does_not_exists}" in str(err.value)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_exists(ctr_client: DockerClient):
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
