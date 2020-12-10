import os

import pytest

from python_on_whales import DockerException, docker
from python_on_whales.components.buildx import BuilderInspectResult
from python_on_whales.test_utils import set_cache_validity_period
from python_on_whales.utils import PROJECT_ROOT

dockerfile_content1 = """
FROM busybox
RUN touch /dada
"""


def test_buildx_build(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    docker.buildx.build(tmp_path)


def test_buildx_build_context_manager(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with docker.buildx.create(use=True):
        docker.buildx.build(tmp_path)


def test_buildx_build_context_manager2(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    buildx_builder = docker.buildx.create()
    docker.buildx.use(buildx_builder)
    with buildx_builder:
        docker.buildx.build(tmp_path)

    # check that the builder doesn't exist
    with pytest.raises(DockerException):
        docker.buildx.inspect(buildx_builder.name)


def test_inspect():
    my_builder = docker.buildx.create(use=True)
    with my_builder:
        assert docker.buildx.inspect(my_builder.name) == my_builder
        assert docker.buildx.inspect() == my_builder


def test_buildx_build_single_tag(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    image = docker.buildx.build(tmp_path, tags="hello1", return_image=True)
    assert "hello1:latest" in image.repo_tags


def test_buildx_build_multiple_tags(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    image = docker.buildx.build(tmp_path, tags=["hello1", "hello2"], return_image=True)
    assert "hello1:latest" in image.repo_tags
    assert "hello2:latest" in image.repo_tags


def test_cache_invalidity(tmp_path):

    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with set_cache_validity_period(100):
        image = docker.buildx.build(
            tmp_path, tags=["hello1", "hello2"], return_image=True
        )
        docker.image.remove("hello1")
        docker.pull("hello-world")
        docker.tag("hello-world", "hello1")
        image.reload()
        assert "hello1:latest" not in image.repo_tags
        assert "hello2:latest" in image.repo_tags


def test_buildx_build_aliases(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    docker.build(tmp_path)
    docker.image.build(tmp_path)


def test_buildx_error(tmp_path):
    with pytest.raises(DockerException) as e:
        docker.buildx.build(tmp_path)

    assert f"docker buildx build {tmp_path}" in str(e.value)


def test_buildx_build_network(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    docker.buildx.build(tmp_path, network="host")


def test_buildx_build_file(tmp_path):
    (tmp_path / "Dockerfile111").write_text(dockerfile_content1)
    docker.buildx.build(tmp_path, file=(tmp_path / "Dockerfile111"))


def test_buildx_create_remove():
    builder = docker.buildx.create()

    docker.buildx.remove(builder)


some_builder_info = """
Name:   blissful_swartz
Driver: docker-container

Nodes:
Name:      blissful_swartz0
Endpoint:  unix:///var/run/docker.sock
Status:    inactive
Platforms:
"""


def test_builder_inspect_result_from_string():
    a = BuilderInspectResult.from_str(some_builder_info)
    assert a.name == "blissful_swartz"
    assert a.driver == "docker-container"


bake_test_dir = PROJECT_ROOT / "tests/python_on_whales/components/bake_tests"
bake_file = bake_test_dir / "docker-bake.hcl"


@pytest.fixture
def change_cwd():
    old_cwd = os.getcwd()
    os.chdir(bake_test_dir)
    yield
    os.chdir(old_cwd)


@pytest.mark.usefixtures("change_cwd")
@pytest.mark.parametrize("only_print", [True, False])
def test_bake(only_print):
    config = docker.buildx.bake(files=[bake_file], print=only_print)
    assert config == {
        "target": {
            "my_out1": {
                "context": "./",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image1:1.0.0"],
                "target": "out1",
            },
            "my_out2": {
                "context": "./",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image2:1.0.0"],
                "target": "out2",
            },
        }
    }


@pytest.mark.usefixtures("change_cwd")
@pytest.mark.parametrize("only_print", [True, False])
def test_bake_with_load(only_print):
    config = docker.buildx.bake(files=[bake_file], load=True, print=only_print)
    assert config == {
        "target": {
            "my_out1": {
                "context": "./",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image1:1.0.0"],
                "target": "out1",
                "output": ["type=docker"],
            },
            "my_out2": {
                "context": "./",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image2:1.0.0"],
                "target": "out2",
                "output": ["type=docker"],
            },
        }
    }


@pytest.mark.usefixtures("change_cwd")
@pytest.mark.parametrize("only_print", [True, False])
def test_bake_with_variables(only_print):
    config = docker.buildx.bake(
        files=[bake_file], print=only_print, variables={"TAG": "3.0.4"}
    )
    assert config == {
        "target": {
            "my_out1": {
                "context": "./",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image1:3.0.4"],
                "target": "out1",
            },
            "my_out2": {
                "context": "./",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image2:3.0.4"],
                "target": "out2",
            },
        }
    }


@pytest.mark.usefixtures("change_cwd")
@pytest.mark.parametrize("only_print", [True, False])
def test_bake_with_variables_2(only_print, monkeypatch):
    monkeypatch.setenv("IMAGE_NAME_1", "dodo")
    config = docker.buildx.bake(
        files=[bake_file], print=only_print, variables={"TAG": "3.0.4"}
    )
    assert config == {
        "target": {
            "my_out1": {
                "context": "./",
                "dockerfile": "Dockerfile",
                "tags": ["dodo:3.0.4"],
                "target": "out1",
            },
            "my_out2": {
                "context": "./",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image2:3.0.4"],
                "target": "out2",
            },
        }
    }


def test_prune():
    docker.buildx.prune(filters=dict(until="3m"))
