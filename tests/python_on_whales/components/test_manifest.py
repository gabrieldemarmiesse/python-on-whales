import json
import os
from typing import Generator

import pytest

from python_on_whales import DockerClient, Image
from python_on_whales.components.manifest.cli_wrapper import (
    ManifestList,
    ManifestListInspectResult,
)
from python_on_whales.test_utils import get_all_jsons, random_name


@pytest.fixture
def manifest(docker_client: DockerClient) -> Generator[ManifestList, None, None]:
    manifest_name = random_name()
    # utilizing old, pre-manifest-list images
    images = ["busybox:1.26", "busybox:1.27.1"]
    docker_client.image.pull(images)
    with docker_client.manifest.create(manifest_name, images) as my_manifest:
        yield my_manifest
    docker_client.image.remove(images)


@pytest.fixture
def platform_variant_manifest(
    docker_client: DockerClient, request: pytest.FixtureRequest
) -> Image:
    image_with_platform_variant = "arm32v7/busybox:1.35"

    def remove_docker_image():
        docker_client.image.remove(image_with_platform_variant)

    request.addfinalizer(remove_docker_image)
    docker_client.image.pull(
        image_with_platform_variant, quiet=True, platform="linux/arm/v7"
    )
    return docker_client.image.inspect(image_with_platform_variant)


@pytest.mark.parametrize("json_file", get_all_jsons("manifests"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ManifestListInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


@pytest.mark.skipif(
    os.environ.get("CI", "false") == "true",
    reason="The creation of manifest doesn't work in github actions for some reason",
)
def test_manifest_create_remove(docker_client: DockerClient, manifest: ManifestList):
    assert isinstance(manifest, ManifestList)


@pytest.mark.skipif(
    os.environ.get("CI", "false") == "true",
    reason="The creation of manifest doesn't work in github actions for some reason",
)
def test_manifest_annotate(docker_client: DockerClient, manifest: ManifestList):
    docker_client.manifest.annotate(
        manifest.name, "busybox:1.26", os="linux", arch="arm64"
    )
    assert manifest.manifests[0].platform.os == "linux"
    assert manifest.manifests[0].platform.architecture == "arm64"


def test_manifest_platform_variant(platform_variant_manifest: Image):
    assert "linux" in repr(platform_variant_manifest.os)
    assert "arm" in repr(platform_variant_manifest.architecture)
    assert "v7" in repr(platform_variant_manifest.variant)
