from unittest.mock import patch

import pytest

from python_on_whales import docker
from python_on_whales.utils import PROJECT_ROOT

bake_test_dir = PROJECT_ROOT / "tests/python_on_whales/components/bake_tests"
bake_file = bake_test_dir / "docker-bake.hcl"


def test_imagetools_inspect_multiarch():
    a = docker.buildx.imagetools.inspect("python:3.13.0")
    assert a.media_type.startswith("application/")


def test_imagetools_inspect_single_image():
    a = docker.buildx.imagetools.inspect(
        "python@sha256:6bb74b8212b18a54d1a3cc03811beccf5497e87d13c2796ce23de76944494829"
    )
    assert a.schema_version == 2
    assert a.config.media_type.startswith("application/")


def test_imagetools_create_single_image():
    a = docker.buildx.imagetools.create(["python:3.13.0"], dry_run=True)
    assert a.media_type.startswith("application/")


def test_imagetools_create_single_image_with_hash():
    a = docker.buildx.imagetools.create(
        [
            "python@sha256:6bb74b8212b18a54d1a3cc03811beccf5497e87d13c2796ce23de76944494829"
        ],
        dry_run=True,
    )
    assert a.schema_version == 2
    assert a.media_type.startswith("application/")


def test_imagetools_create_new_image_with_tag(docker_registry):
    busybox = docker.pull("busybox:1")
    base_image = f"{docker_registry}/test:image1"
    docker.tag(busybox, base_image)
    docker.push(base_image)
    new_image = f"{docker_registry}/test:image2"
    docker.buildx.imagetools.create([base_image], tags=[new_image])
    docker.pull(new_image)


def test_imagetools_create_new_image_with_tags(docker_registry):
    busybox = docker.pull("busybox:1")
    base_image = f"{docker_registry}/test:image1"
    docker.tag(busybox, base_image)
    docker.push(base_image)
    new_image_2 = f"{docker_registry}/test:image2"
    new_image_3 = f"{docker_registry}/test:image3"
    docker.buildx.imagetools.create([base_image], tags=[new_image_2, new_image_3])
    docker.pull([new_image_2, new_image_3])


def test_imagetools_append(docker_registry):
    busybox = docker.pull("busybox:1")
    alpine = docker.pull("alpine")
    base_image_busybox = f"{docker_registry}/test:busybox"
    base_image_alpine = f"{docker_registry}/test:alpine"
    docker.tag(busybox, base_image_busybox)
    docker.tag(alpine, base_image_alpine)
    docker.push(base_image_busybox)
    docker.push(base_image_alpine)
    new_image = f"{docker_registry}/test:image2"
    docker.buildx.imagetools.create([base_image_busybox], tags=[new_image])
    docker.buildx.imagetools.create([base_image_alpine], tags=[new_image], append=True)
    docker.pull(new_image)


def test_imagetools_create_annotations_type_validation():
    with pytest.raises(TypeError) as err:
        docker.buildx.imagetools.create(
            ["python:3.13.0"], annotations="not-a-dict", dry_run=True
        )
    assert "must be a dict" in str(err.value)


def test_imagetools_create_with_annotations_command_construction():
    annotations = {
        "index:org.opencontainers.image.source": "https://github.com/user/repo",
        "index:org.opencontainers.image.description": "Test image",
    }

    manifest = docker.buildx.imagetools.create(
        sources=["python:3.13.0"],
        tags=["myrepo/myimage:latest"],
        annotations=annotations,
        dry_run=True,
    )

    assert len(manifest.annotations) == 2
    assert manifest.annotations["org.opencontainers.image.source"] == "https://github.com/user/repo"
    assert manifest.annotations["org.opencontainers.image.description"] == "Test image"

