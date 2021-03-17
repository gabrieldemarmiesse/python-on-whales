from python_on_whales import docker


def test_imagetools_inspect_multiarch():
    a = docker.buildx.imagetools.inspect("python:3.7.0")
    assert a.media_type.startswith("application/")


def test_imagetools_inspect_single_image():
    a = docker.buildx.imagetools.inspect(
        "python@sha256:b48b88687b1376f3135a048c8cdaccad4e8dd1af2f345c693a39b75a5683a3eb"
    )
    assert a.schema_version == 2
    assert a.config.media_type.startswith("application/")
