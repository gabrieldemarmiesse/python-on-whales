import pytest

from docker_cli_wrapper import DockerException, docker

dockerfile_content1 = """
FROM busybox
RUN touch /dada
"""


def test_buildx_build(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    docker.buildx.build(tmp_path)


def test_buildx_error(tmp_path):
    with pytest.raises(DockerException) as e:
        docker.buildx.build(tmp_path)

    assert f"docker buildx build {tmp_path}" in str(e.value)
