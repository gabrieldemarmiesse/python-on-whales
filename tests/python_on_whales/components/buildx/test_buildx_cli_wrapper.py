import os
import tarfile

import pytest

from python_on_whales import docker
from python_on_whales.components.buildx.models import BuilderInspectResult
from python_on_whales.exceptions import DockerException
from python_on_whales.test_utils import set_cache_validity_period
from python_on_whales.utils import PROJECT_ROOT

dockerfile_content1 = """
FROM busybox
RUN touch /dada
"""

dockerfile_content2 = """
FROM busybox
COPY --from=test_context README.md /README.md
"""

dockerfile_content3 = """
FROM test_context
RUN touch /dada
"""

dockerfile_content4 = """
FROM busybox
COPY --from=test_context /dada /dada
"""


@pytest.fixture
def with_docker_driver():
    current_builder = docker.buildx.inspect()
    docker.buildx.use("default")
    yield
    docker.buildx.use(current_builder)


@pytest.fixture
def with_container_driver():
    current_builder = docker.buildx.inspect()
    with docker.buildx.create(use=True):
        yield
    docker.buildx.use(current_builder)


@pytest.fixture
def prune_all():
    docker.buildx.prune(all=True)


@pytest.fixture
def with_oci_layout_compliant_dir(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)

    # Build the oci layout compliant directory
    tar_path = os.path.join(tmp_path, "oci-layout.tar")
    oci_folder_path = os.path.join(tmp_path, "oci-layout")

    current_builder = docker.buildx.inspect()
    with docker.buildx.create(use=True):
        docker.buildx.build(tmp_path, output={"type": "oci", "dest": tar_path})
    docker.buildx.use(current_builder)

    # Extract tar to directory
    with tarfile.open(tar_path) as tar:
        tar.extractall(oci_folder_path)


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    my_image = docker.buildx.build(tmp_path)
    assert my_image.size > 1000


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_streaming_logs(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    output = list(docker.buildx.build(tmp_path, stream_logs=True))
    assert len(output) > 1
    for line in output:
        assert line != ""


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_streaming_logs_with_decode_error_handling(tmp_path):
    # This will simulate buildx clipping log output in the middle of a UTF-8 character
    bad_encoding_dockerfile = (
        dockerfile_content1
        + """
    RUN printf '\\xE2\\x9E'
    """
    )
    (tmp_path / "Dockerfile").write_text(bad_encoding_dockerfile)
    output = list(docker.buildx.build(tmp_path, cache=False, stream_logs=True))
    assert len([x for x in output if "�" in x]) == 1
    assert "#7 DONE" in output[-1]


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_load_docker_driver(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    my_image = docker.buildx.build(tmp_path, load=True)
    assert my_image.size > 1000


def test_legacy_build_simple_case(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    my_image = docker.legacy_build(tmp_path)
    assert my_image.size > 1000


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_push_registry(tmp_path, docker_registry):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with docker.buildx.create(use=True, driver_options=dict(network="host")):
        output = docker.buildx.build(
            tmp_path, push=True, tags=f"{docker_registry}/dodo"
        )
    assert output is None
    docker.pull(f"{docker_registry}/dodo")


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_push_registry_override_builder(tmp_path, docker_registry):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with docker.buildx.create(driver_options=dict(network="host")) as my_builder:
        output = docker.buildx.build(
            tmp_path, push=True, tags=f"{docker_registry}/dodo", builder=my_builder
        )
    assert output is None
    docker.pull(f"{docker_registry}/dodo")


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_caching(tmp_path, docker_registry):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    cache = f"{docker_registry}/project:cache"
    with docker.buildx.create(driver_options=dict(network="host"), use=True):
        docker.buildx.build(tmp_path, cache_to=cache)

    with docker.buildx.create(driver_options=dict(network="host"), use=True):
        docker.buildx.build(tmp_path, cache_from=cache)


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_caching_both_name_time(tmp_path, docker_registry):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    cache = f"{docker_registry}/project:cache"
    with docker.buildx.create(driver_options=dict(network="host"), use=True):
        docker.buildx.build(tmp_path, cache_to=cache, cache_from=cache)

    with docker.buildx.create(driver_options=dict(network="host"), use=True):
        docker.buildx.build(tmp_path, cache_to=cache, cache_from=cache)


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_caching_dict_form(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with docker.buildx.create(driver_options=dict(network="host"), use=True):
        docker.buildx.build(
            tmp_path, cache_to=dict(type="local", dest=tmp_path / "cache", mode="max")
        )

    with docker.buildx.create(driver_options=dict(network="host"), use=True):
        docker.buildx.build(
            tmp_path, cache_from=dict(type="local", src=tmp_path / "cache")
        )


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_caching_list_form(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with docker.buildx.create(driver_options=dict(network="host"), use=True):
        docker.buildx.build(
            tmp_path,
            cache_from=[
                dict(type="local", src=tmp_path / "cache"),
                dict(type="local", src=tmp_path / "cache2"),
            ],
        )


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_output_type_registry(tmp_path, docker_registry):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with docker.buildx.create(use=True, driver_options=dict(network="host")):
        output = docker.buildx.build(
            tmp_path, output=dict(type="registry"), tags=f"{docker_registry}/dodo"
        )
    assert output is None
    docker.pull(f"{docker_registry}/dodo")


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_push_registry_multiple_tags(tmp_path, docker_registry):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    tags = [f"{docker_registry}/dodo:1", f"{docker_registry}/dada:1"]
    with docker.buildx.create(use=True, driver_options=dict(network="host")):
        output = docker.buildx.build(tmp_path, push=True, tags=tags)
    assert output is None
    docker.pull(f"{docker_registry}/dodo:1")
    docker.pull(f"{docker_registry}/dada:1")


@pytest.mark.usefixtures("with_container_driver")
def test_buildx_build_load_container_driver(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    my_image = docker.buildx.build(tmp_path, load=True)

    # can only be fixed by fixing https://github.com/docker/buildx/issues/420
    assert my_image is None


@pytest.mark.usefixtures("with_container_driver")
def test_buildx_build_load_container_driver_tag(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with docker.buildx.build(tmp_path, load=True, tags="my_tag:1") as my_image:
        assert my_image.repo_tags == ["my_tag:1"]


def test_legacy_build_tag(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with docker.legacy_build(tmp_path, tags="my_tag:1") as my_image:
        assert my_image.repo_tags == ["my_tag:1"]


@pytest.mark.usefixtures("with_container_driver")
def test_buildx_build_load_container_driver_tags(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with docker.buildx.build(
        tmp_path, load=True, tags=["my_tag:1", "other_tag:2"]
    ) as my_image:
        assert set(my_image.repo_tags) == {"my_tag:1", "other_tag:2"}


@pytest.mark.usefixtures("with_container_driver")
def test_buildx_build_container_driver(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    my_image = docker.buildx.build(tmp_path)
    assert my_image is None
    # by default, loading isn't activated with the container driver.


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_output_local_docker_driver(tmp_path):
    _test_buildx_build_output_local(tmp_path)


@pytest.mark.usefixtures("with_container_driver")
def test_buildx_build_output_local_container_driver(tmp_path):
    _test_buildx_build_output_local(tmp_path)


def _test_buildx_build_output_local(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    my_image = docker.buildx.build(
        tmp_path, output=dict(type="local", dest=tmp_path / "my_image")
    )
    assert my_image is None
    assert (tmp_path / "my_image/dada").is_file()


def test_multiarch_build(tmp_path, docker_registry):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    tags = [f"{docker_registry}/dodo:1"]
    with docker.buildx.create(use=True, driver_options=dict(network="host")):
        output = docker.buildx.build(
            tmp_path, push=True, tags=tags, platforms=["linux/amd64", "linux/arm64"]
        )
    assert output is None
    docker.pull(f"{docker_registry}/dodo:1")


@pytest.mark.usefixtures("with_container_driver")
@pytest.mark.parametrize(
    "kwargs",
    [
        dict(sbom=True),
        dict(provenance=True),
        dict(attest=dict(type="provenance", mode="min")),
        dict(provenance=dict(mode="max")),
    ],
)
def test_buildx_build_attestations(tmp_path, kwargs):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    docker.buildx.build(tmp_path, **kwargs)


# Does the build work when passing extra contexts
# without making use of them in the Dockerfile
@pytest.mark.usefixtures("with_container_driver")
def test_buildx_build_build_context1(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    docker.buildx.build(tmp_path, build_contexts=dict(test_context="."))


# Does the build work when passing extra contexts
# when the Dockerfile does make use of them
@pytest.mark.usefixtures("with_container_driver")
@pytest.mark.parametrize(
    "test_context",
    [
        # Test with local directory
        PROJECT_ROOT,
        # Test with git repo
        "https://github.com/gabrieldemarmiesse/python-on-whales.git",
    ],
)
def test_buildx_build_build_context2(tmp_path, test_context):
    (tmp_path / "Dockerfile").write_text(dockerfile_content2)
    docker.buildx.build(tmp_path, build_contexts=dict(test_context=test_context))


# Test with oci layout compliant directory
@pytest.mark.usefixtures("with_oci_layout_compliant_dir")
@pytest.mark.usefixtures("with_container_driver")
def test_buildx_build_build_context_oci(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content4)
    docker.buildx.build(
        tmp_path,
        build_contexts=dict(
            test_context=f"oci-layout://{os.path.join(tmp_path, 'oci-layout')}"
        ),
    )


# Test with docker image
@pytest.mark.usefixtures("with_container_driver")
def test_buildx_build_build_context_image(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content3)
    docker.buildx.build(
        tmp_path,
        build_contexts=dict(test_context="docker-image://busybox:1.36.0"),
    )


# Does the build fail when NOT passing extra contexts
# when the dockerfile does make use of them
@pytest.mark.usefixtures("with_container_driver")
def test_buildx_build_build_context_fail(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content2)
    with pytest.raises(DockerException):
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
def test_buildx_build_single_tag(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    image = docker.buildx.build(tmp_path, tags="hello1")
    assert "hello1:latest" in image.repo_tags


def test_legacy_build_single_tag(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    image = docker.legacy_build(tmp_path, tags="hello1")
    assert "hello1:latest" in image.repo_tags


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_multiple_tags(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    image = docker.buildx.build(tmp_path, tags=["hello1", "hello2"])
    assert "hello1:latest" in image.repo_tags
    assert "hello2:latest" in image.repo_tags


def test_legacy_build_multiple_tags(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    image = docker.legacy_build(tmp_path, tags=["hello1", "hello2"])
    assert "hello1:latest" in image.repo_tags
    assert "hello2:latest" in image.repo_tags


@pytest.mark.usefixtures("with_docker_driver")
def test_cache_invalidity(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    with set_cache_validity_period(100):
        image = docker.buildx.build(tmp_path, tags=["hello1", "hello2"])
        docker.image.remove("hello1")
        docker.pull("hello-world")
        docker.tag("hello-world", "hello1")
        image.reload()
        assert "hello1:latest" not in image.repo_tags
        assert "hello2:latest" in image.repo_tags


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_aliases(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    docker.build(tmp_path)
    docker.image.build(tmp_path)


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_error(tmp_path):
    with pytest.raises(DockerException) as e:
        docker.buildx.build(tmp_path)

    assert "docker buildx build" in str(e.value)
    assert str(tmp_path) in str(e.value)


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_network(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    docker.buildx.build(tmp_path, network="host")


def test_legacy_build_network(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)
    docker.legacy_build(tmp_path, network="host")


@pytest.mark.usefixtures("with_docker_driver")
def test_buildx_build_file(tmp_path):
    (tmp_path / "Dockerfile111").write_text(dockerfile_content1)
    docker.buildx.build(tmp_path, file=(tmp_path / "Dockerfile111"))


def test_legacy_build_file(tmp_path):
    (tmp_path / "Dockerfile111").write_text(dockerfile_content1)
    docker.legacy_build(tmp_path, file=(tmp_path / "Dockerfile111"))


def test_buildx_create_remove():
    builder = docker.buildx.create()

    docker.buildx.remove(builder)


def test_buildx_create_remove_with_platforms():
    builder = docker.buildx.create(platforms=["linux/amd64", "linux/arm64"])

    assert builder.platforms == ["linux/amd64*", "linux/arm64*"]

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

some_builder_info_with_platforms = """
Name:   blissful_swartz
Driver: docker-container

Nodes:
Name:      blissful_swartz0
Endpoint:  unix:///var/run/docker.sock
Status:    running
Platforms: linux/amd64, linux/arm64
"""


def test_builder_inspect_result_from_string():
    a = BuilderInspectResult.from_str(some_builder_info)
    assert a.name == "blissful_swartz"
    assert a.driver == "docker-container"
    assert a.status == "inactive"
    assert a.platforms == []


def test_builder_inspect_result_platforms_from_string():
    a = BuilderInspectResult.from_str(some_builder_info_with_platforms)
    assert a.name == "blissful_swartz"
    assert a.driver == "docker-container"
    assert a.status == "running"
    assert a.platforms == ["linux/amd64", "linux/arm64"]


bake_test_dir = PROJECT_ROOT / "tests/python_on_whales/components/bake_tests"
bake_file = bake_test_dir / "docker-bake.hcl"


@pytest.fixture
def change_cwd():
    old_cwd = os.getcwd()
    os.chdir(bake_test_dir)
    yield
    os.chdir(old_cwd)


@pytest.mark.usefixtures("with_docker_driver")
@pytest.mark.usefixtures("change_cwd")
@pytest.mark.parametrize("only_print", [True, False])
def test_bake(only_print):
    config = docker.buildx.bake(files=[bake_file], print=only_print)
    assert config == {
        "group": {"default": {"targets": ["my_out1", "my_out2"]}},
        "target": {
            "my_out1": {
                "context": ".",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image1:1.0.0"],
                "target": "out1",
            },
            "my_out2": {
                "context": ".",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image2:1.0.0"],
                "target": "out2",
            },
        },
    }


@pytest.mark.usefixtures("with_docker_driver")
@pytest.mark.usefixtures("change_cwd")
@pytest.mark.parametrize("only_print", [True, False])
def test_bake_with_load(only_print):
    config = docker.buildx.bake(files=[bake_file], load=True, print=only_print)
    assert config == {
        "group": {"default": {"targets": ["my_out1", "my_out2"]}},
        "target": {
            "my_out1": {
                "context": ".",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image1:1.0.0"],
                "target": "out1",
                "output": ["type=docker"],
            },
            "my_out2": {
                "context": ".",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image2:1.0.0"],
                "target": "out2",
                "output": ["type=docker"],
            },
        },
    }


@pytest.mark.usefixtures("with_docker_driver")
@pytest.mark.usefixtures("change_cwd")
@pytest.mark.parametrize("only_print", [True, False])
def test_bake_with_variables(only_print):
    config = docker.buildx.bake(
        files=[bake_file], print=only_print, variables={"TAG": "3.0.4"}
    )
    assert config == {
        "group": {"default": {"targets": ["my_out1", "my_out2"]}},
        "target": {
            "my_out1": {
                "context": ".",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image1:3.0.4"],
                "target": "out1",
            },
            "my_out2": {
                "context": ".",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image2:3.0.4"],
                "target": "out2",
            },
        },
    }


@pytest.mark.usefixtures("with_docker_driver")
@pytest.mark.usefixtures("change_cwd")
@pytest.mark.parametrize("only_print", [True, False])
def test_bake_with_variables_2(only_print, monkeypatch):
    monkeypatch.setenv("IMAGE_NAME_1", "dodo")
    config = docker.buildx.bake(
        files=[bake_file], print=only_print, variables={"TAG": "3.0.4"}
    )
    assert config == {
        "group": {"default": {"targets": ["my_out1", "my_out2"]}},
        "target": {
            "my_out1": {
                "context": ".",
                "dockerfile": "Dockerfile",
                "tags": ["dodo:3.0.4"],
                "target": "out1",
            },
            "my_out2": {
                "context": ".",
                "dockerfile": "Dockerfile",
                "tags": ["pretty_image2:3.0.4"],
                "target": "out2",
            },
        },
    }


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


@pytest.mark.usefixtures("with_docker_driver")
@pytest.mark.usefixtures("prune_all")
def test_prune_all_empty():
    logs = docker.buildx.prune(all=True, stream_logs=True)
    logs = list(logs)
    assert len(logs) == 1  # nothing reclaimable
    assert logs[0] == "Total:\t0B\n"


@pytest.mark.usefixtures("with_docker_driver")
def test_prune(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)

    with docker.buildx.create(driver_options=dict(network="host"), use=True):
        docker.buildx.build(
            tmp_path, cache_from=dict(type="local", src=tmp_path / "cache")
        )
        logs = list(docker.buildx.prune(all=True, stream_logs=True))
        table_first_row_categories = logs[0]
        table_total_freed_space = logs[-1]
        random_row_with_reclaimable = logs[1]
        assert (
            table_first_row_categories
            == "ID\t\t\t\t\t\tRECLAIMABLE\tSIZE\t\tLAST ACCESSED\n"
        )
        assert "Total:" in table_total_freed_space
        assert "true" in random_row_with_reclaimable
        assert len(logs) >= 2  # table header plus at least one freed file


@pytest.mark.usefixtures("with_docker_driver")
def test_prune_cache_mode_max(tmp_path):
    (tmp_path / "Dockerfile").write_text(dockerfile_content1)

    with docker.buildx.create(driver_options=dict(network="host"), use=True):
        docker.buildx.build(
            tmp_path, cache_to=dict(type="local", dest=tmp_path / "cache", mode="max")
        )
        logs = list(docker.buildx.prune(all=True, stream_logs=True))
        table_first_row_categories = logs[0]
        table_total_freed_space = logs[-1]
        random_row_with_reclaimable = logs[1]
        assert (
            table_first_row_categories
            == "ID\t\t\t\t\t\tRECLAIMABLE\tSIZE\t\tLAST ACCESSED\n"
        )
        assert "Total:" in table_total_freed_space
        assert "true" in random_row_with_reclaimable
        assert len(logs) >= 2  # table header plus at least one freed file


def test_list():
    builders = docker.buildx.list()
    assert docker.buildx.inspect() in builders
    assert docker.buildx.inspect("default") in builders
    for builder in builders:
        assert builder.driver in ["docker", "docker-container"]
