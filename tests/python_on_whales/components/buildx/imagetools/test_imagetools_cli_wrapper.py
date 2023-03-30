from python_on_whales import docker
from python_on_whales.utils import PROJECT_ROOT

bake_test_dir = PROJECT_ROOT / "tests/python_on_whales/components/bake_tests"
bake_file = bake_test_dir / "docker-bake.hcl"


def test_imagetools_inspect_multiarch():
    a = docker.buildx.imagetools.inspect("python:3.7.0")
    assert a.media_type.startswith("application/")


def test_imagetools_inspect_single_image():
    a = docker.buildx.imagetools.inspect(
        "python@sha256:b48b88687b1376f3135a048c8cdaccad4e8dd1af2f345c693a39b75a5683a3eb"
    )
    assert a.schema_version == 2
    assert a.config.media_type.startswith("application/")


def test_imagetools_create_single_image():
    a = docker.buildx.imagetools.create(["python:3.7.0"], dry_run=True)
    assert a.media_type.startswith("application/")


def test_imagetools_create_single_image_with_hash():
    a = docker.buildx.imagetools.create(
        [
            "python@sha256:b48b88687b1376f3135a048c8cdaccad4e8dd1af2f345c693a39b75a5683a3eb"
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
