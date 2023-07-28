import json
import os

import pytest

from python_on_whales import docker
from python_on_whales.components.manifest.cli_wrapper import (
    ManifestList,
    ManifestListInspectResult,
)
from python_on_whales.test_utils import get_all_jsons, random_name


@pytest.fixture
def with_manifest():
    manifest_name = random_name()
    # utilizing old, pre-manifest-list images
    images = ["busybox:1.26", "busybox:1.27.1"]
    docker.image.pull(images)
    with docker.manifest.create(manifest_name, images) as my_manifest:
        yield my_manifest
    docker.image.remove(images)


@pytest.mark.parametrize("json_file", get_all_jsons("manifests"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ManifestListInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


@pytest.mark.skipif(
    os.environ.get("CI", "false") == "true",
    reason="The creation of manifest doesn't work in github actions for some reason",
)
def test_manifest_create_remove(with_manifest):
    assert isinstance(with_manifest, ManifestList)


@pytest.mark.skipif(
    os.environ.get("CI", "false") == "true",
    reason="The creation of manifest doesn't work in github actions for some reason",
)
def test_manifest_annotate(with_manifest):
    docker.manifest.annotate(
        with_manifest.name, "busybox:1.26", os="linux", arch="arm64"
    )
    assert with_manifest.manifests[0].platform.os == "linux"
    assert with_manifest.manifests[0].platform.architecture == "arm64"
