import pytest

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

def test_imagetools_create_multiarch():
    a = docker.buildx.imagetools.create("python:3.7.0")
    assert a.media_type.startswith("application/")


def test_imagetools_create_single_image():
    a = docker.buildx.imagetools.inspect(
        "python@sha256:b48b88687b1376f3135a048c8cdaccad4e8dd1af2f345c693a39b75a5683a3eb"
    )
    assert a.schema_version == 2
    assert a.config.media_type.startswith("application/")


def test_builder_name():
    my_builder = docker.buildx.create(name="some_builder")
    with my_builder:
        assert my_builder.name == "some_builder"


def test_builder_options():
    my_builder = docker.buildx.create(driver_options=dict(network="host"))
    my_builder.remove()


def test_builder_set_driver():
    my_builder = docker.buildx.create(driver="docker-container")
    my_builder.remove()


def test_use_builder():
    my_builder = docker.buildx.create()
    with my_builder:
        docker.buildx.use(my_builder)
        docker.buildx.use("default")
        docker.buildx.use(my_builder, default=True, global_=True)

@pytest.mark.usefixtures("with_docker_driver")
@pytest.mark.usefixtures("change_cwd")
def test_bake_stream_logs(monkeypatch):
    monkeypatch.setenv("IMAGE_NAME_1", "dodo")
    output = docker.buildx.bake(
        files=[bake_file], variables={"TAG": "3.0.4"}, stream_logs=True
    )
    output = list(output)
    assert output[0].startswith("#")
    assert output[-1].startswith("#")
