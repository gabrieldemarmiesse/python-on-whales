import json
import signal
import tempfile
import time
from datetime import datetime, timedelta
from os import makedirs, remove
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import pytz

import python_on_whales
from python_on_whales import DockerClient, DockerException
from python_on_whales.components.compose.models import ComposeConfig
from python_on_whales.exceptions import NoSuchImage
from python_on_whales.test_utils import get_all_jsons
from python_on_whales.utils import PROJECT_ROOT

pytestmark = pytest.mark.skipif(
    not python_on_whales.docker.compose.is_installed(),
    reason="Those tests need docker compose.",
)

docker = DockerClient(
    compose_files=[
        PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
    ],
    compose_compatibility=True,
)


def mock_KeyboardInterrupt(signum, frame):
    raise KeyboardInterrupt("Time is up")


def test_build_empty_list_of_services():
    previous_images = set(docker.image.list())
    docker.compose.build([])
    assert previous_images == set(docker.image.list())


def test_create_empty_list_of_services():
    previous_containers = set(docker.ps(all=True))
    docker.compose.create([])
    assert previous_containers == set(docker.ps(all=True))


def test_kill_empty_list_of_services():
    docker.compose.up(["my_service", "busybox", "alpine"], detach=True)
    time.sleep(1)
    all_running_containers = set(docker.ps())
    docker.compose.kill([])
    assert all_running_containers == set(docker.ps())
    docker.compose.down(timeout=1)


def test_wait_for_service():
    docker = python_on_whales.DockerClient(
        compose_files=[Path(__file__).parent / "compose-with-healthcheck.yml"]
    )
    # ensure environment is clean
    docker.compose.down(timeout=1, volumes=True)

    docker.compose.up(["my_redis"], detach=True)
    # this should be too fast and the healthcheck shouldn't be ready
    container = docker.compose.ps()[0]
    assert container.state.health.status == "starting"
    docker.compose.down(timeout=1, volumes=True)

    # now we use wait, and we check that it's healthy as soon as the function returns
    docker.compose.up(["my_redis"], detach=True, wait=True)
    container = docker.compose.ps()[0]
    assert container.state.health.status == "healthy"
    docker.compose.down(timeout=1, volumes=True)

    # now we use wait with timeout and check that timeout respects
    with pytest.raises(DockerException) as exc_info:
        list(
            docker.compose.up(
                ["unhealthy_service"],
                detach=True,
                wait=True,
                wait_timeout=1,
                stream_logs=True,
            )
        )
    assert "application not healthy after" in exc_info.value.stderr
    docker.compose.down(timeout=1, volumes=True)


def test_pause_empty_list_of_services():
    docker.compose.up(["my_service", "busybox", "alpine"], detach=True)
    time.sleep(1)
    number_of_paused_containers = len([x for x in docker.ps() if x.state.paused])
    docker.compose.pause([])
    assert number_of_paused_containers == len(
        [x for x in docker.ps() if x.state.paused]
    )
    docker.compose.down(timeout=1)


def test_remove_empty_list_of_services():
    docker.compose.up(["my_service", "busybox", "alpine"], detach=True)
    time.sleep(1)
    number_of_containers = len(docker.ps())
    docker.compose.rm([], stop=True)
    assert number_of_containers == len(docker.ps())
    docker.compose.down(timeout=1)


def test_pull_empty_list_of_services():
    len_list_of_images = len(docker.image.list())
    docker.compose.pull([])
    assert len_list_of_images == len(docker.image.list())


def test_push_empty_list_of_services():
    docker.compose.push([])


def test_compose_project_name():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
        ],
        compose_project_name="dudu",
        compose_compatibility=True,
    )
    docker.compose.up(["busybox", "alpine"], detach=True)
    containers = docker.compose.ps()
    container_names = set(x.name for x in containers)
    assert container_names == {"dudu_busybox_1", "dudu_alpine_1"}
    docker.compose.down(timeout=1)


def test_docker_compose_build():
    docker.compose.build()
    docker.compose.build(["my_service"])
    docker.compose.build("my_service")
    docker.image.remove("some_random_image")


def test_docker_compose_build_stream():
    logs = list(docker.compose.build(["my_service"], stream_logs=True))
    assert len(logs) >= 3
    logs_as_big_binary = b""
    for log_type, log_value in logs:
        assert log_type in ("stdout", "stderr")
        logs_as_big_binary += log_value

    assert b"load .dockerignore" in logs_as_big_binary
    assert b"DONE" in logs_as_big_binary

    docker.image.remove("some_random_image")


def test_docker_compose_build_with_arguments():
    docker.compose.build(
        build_args={"PYTHON_VERSION": "3.7"},
        cache=False,
        progress="plain",
        pull=True,
        quiet=True,
    )
    docker.image.remove("some_random_image")


def test_docker_compose_up_down():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_ends_quickly.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(["busybox", "alpine"])
    output_of_down = docker.compose.down(timeout=1)
    assert output_of_down is None
    assert docker.compose.ps() == []


def test_docker_compose_up_down_streaming():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_ends_quickly.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(["busybox", "alpine"])
    logs = list(docker.compose.down(timeout=1, stream_logs=True))

    assert len(logs) >= 3
    logs_as_big_binary = b""
    for log_type, log_value in logs:
        assert log_type in ("stdout", "stderr")
        logs_as_big_binary += log_value

    assert b"Removed" in logs_as_big_binary
    assert b"Container components_alpine_1" in logs_as_big_binary


def test_docker_compose_down_services():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_with_container_names.yml"
        ],
        compose_compatibility=True,
        compose_project_name="test_docker_compose_down_services",
    )

    docker.compose.up(["busybox", "alpine"], detach=True)
    assert len(docker.compose.ps()) == 2

    output_of_down = docker.compose.down(services=["busybox"])
    assert output_of_down is None
    assert len(docker.compose.ps()) == 1
    active_container = docker.compose.ps()[0]
    assert (
        active_container.name == "alpine"
    ), f"actual container name: {active_container.name}"

    output_of_down = docker.compose.down(services=["alpine"])
    assert output_of_down is None
    assert docker.compose.ps() == []


def test_docker_compose_down_no_services():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_with_container_names.yml"
        ],
        compose_compatibility=True,
        compose_project_name="test_docker_compose_down_no_services",
    )
    docker.compose.up(["busybox", "alpine"], detach=True)
    initial_containers = docker.compose.ps()
    assert len(initial_containers) == 2

    output_of_down = docker.compose.down(services=[])
    assert output_of_down is None
    final_containers = docker.compose.ps()
    assert final_containers == initial_containers

    output_of_down = docker.compose.down()
    assert output_of_down is None
    assert docker.compose.ps() == []


@patch("python_on_whales.components.compose.cli_wrapper.run")
def test_docker_compose_cli_down_all_services(run_mock: Mock):
    docker.compose.down()
    run_mock.assert_called_once_with(
        docker.client_config.docker_compose_cmd + ["down"],
        capture_stderr=False,
        capture_stdout=False,
    )


@patch("python_on_whales.components.compose.cli_wrapper.run")
def test_docker_compose_cli_down_multiple_services(run_mock: Mock):
    test_services = ["test_a", "test_b"]
    docker.compose.down(services=test_services)
    run_mock.assert_called_once_with(
        docker.client_config.docker_compose_cmd + ["down"] + test_services,
        capture_stderr=False,
        capture_stdout=False,
    )


@patch("python_on_whales.components.compose.cli_wrapper.run")
def test_docker_compose_cli_down_single_service(run_mock: Mock):
    test_service = "test_a"
    docker.compose.down(services=test_service)
    run_mock.assert_called_once_with(
        docker.client_config.docker_compose_cmd + ["down"] + [test_service],
        capture_stderr=False,
        capture_stdout=False,
    )


@patch("python_on_whales.components.compose.cli_wrapper.run")
def test_docker_compose_cli_down_services_no_op(run_mock: Mock):
    docker.compose.down(services=[])
    run_mock.assert_not_called()


def test_no_containers():
    assert docker.compose.ps() == []


def test_docker_compose_up_detach_down():
    docker.compose.up(["my_service", "busybox", "alpine"], detach=True)
    docker.compose.down(timeout=1)


def test_docker_compose_up_detach_down_with_scales():
    docker.compose.up(
        ["my_service", "busybox", "alpine"],
        detach=True,
        scales={"busybox": 2, "alpine": 3},
    )
    assert len(docker.compose.ps()) == 6

    docker.compose.up(
        ["my_service", "busybox", "alpine"],
        detach=True,
        scales={"busybox": 2, "alpine": 5},
    )
    assert len(docker.compose.ps()) == 8

    docker.compose.down(timeout=1)


def test_docker_compose_pause_unpause():
    docker.compose.up(["my_service", "busybox", "alpine"], detach=True)
    docker.compose.pause()
    for container in docker.compose.ps():
        assert container.state.paused

    docker.compose.unpause()
    for container in docker.compose.ps():
        assert not container.state.paused

    docker.compose.pause(["my_service", "busybox"])

    assert docker.container.inspect("components_my_service_1").state.paused
    assert docker.container.inspect("components_busybox_1").state.paused

    docker.compose.down(timeout=1)


def test_docker_compose_create_down():
    create_result = docker.compose.create()
    assert create_result is None
    docker.compose.down()


def test_docker_compose_create_stream_down():
    docker.compose.down()
    logs = list(
        docker.compose.create(["my_service", "busybox", "alpine"], stream_logs=True)
    )
    assert len(logs) >= 2
    full_logs_as_binary = b"".join(log for _, log in logs)
    assert b"Creating" in full_logs_as_binary
    assert b"components_busybox_1" in full_logs_as_binary
    docker.compose.down()


def test_docker_compose_config():
    compose_config = docker.compose.config()
    assert compose_config.services["alpine"].image == "alpine:latest"

    compose_config = docker.compose.config(return_json=True)
    assert compose_config["services"]["alpine"]["image"] == "alpine:latest"


def test_docker_compose_create_extra_options_down():
    docker.compose.create(build=True, force_recreate=True)
    docker.compose.create(build=True, force_recreate=True)
    docker.compose.create(no_build=True, no_recreate=True)
    docker.compose.down()


def test_docker_compose_up_detach_down_extra_options():
    docker.compose.up(["my_service", "busybox", "alpine"], detach=True)
    docker.compose.down(remove_orphans=True, remove_images="all", timeout=3)


def test_docker_compose_up_build():
    docker.compose.up(["my_service", "busybox", "alpine"], build=True, detach=True)
    with docker.image.inspect("some_random_image"):
        docker.compose.down()


def test_docker_compose_up_stream():
    logs = list(
        docker.compose.up(
            ["my_service", "busybox", "alpine"],
            build=True,
            stream_logs=True,
            detach=True,
            recreate=True,
        )
    )
    assert len(logs) >= 2
    full_logs_as_binary = b"".join(log for _, log in logs)
    assert b"components_alpine_1" in full_logs_as_binary
    assert b"components_my_service_1" in full_logs_as_binary
    assert b"components_busybox_1" in full_logs_as_binary
    docker.compose.down()


def test_docker_compose_up_stop_rm():
    docker.compose.up(["my_service", "busybox", "alpine"], build=True, detach=True)
    docker.compose.stop(timeout=timedelta(seconds=3))
    docker.compose.rm(volumes=True)


def test_docker_compose_stop_stream():
    docker.compose.up(["my_service", "busybox", "alpine"], detach=True)
    logs = list(docker.compose.stop(stream_logs=True))
    assert len(logs) >= 2
    full_logs_as_binary = b"".join(log for _, log in logs)
    assert b"Container components_busybox_1  Stopping" in full_logs_as_binary
    assert b"Container components_busybox_1  Stopped" in full_logs_as_binary


def test_docker_compose_up_rm():
    docker.compose.up(["my_service", "busybox", "alpine"], build=True, detach=True)
    docker.compose.rm(stop=True, volumes=True)


def test_docker_compose_up_down_some_services():
    docker.compose.up(["my_service", "busybox"], detach=True)
    docker.compose.down(timeout=1)


def test_docker_compose_up_pull_never():
    try:
        docker.image.remove("alpine")
    except DockerException:
        pass
    with pytest.raises(DockerException):
        docker.compose.up(["alpine"], pull="never")


def test_docker_compose_up_no_recreate():
    docker.compose.up(["busybox"], detach=True)
    containers = docker.compose.ps()
    container_id = containers[0].id
    docker.compose.up(["busybox"], scales={"busybox": 2}, detach=True, recreate=False)
    container_ids = set(x.id for x in docker.compose.ps())
    assert container_id in container_ids
    docker.compose.down(timeout=1)


def test_docker_compose_ps():
    docker.compose.up(["my_service", "busybox"], detach=True)
    containers = docker.compose.ps()
    names = set(x.name for x in containers)
    assert names == {"components_my_service_1", "components_busybox_1"}
    containers = docker.compose.ps(["my_service"])
    names = set(x.name for x in containers)
    assert names == {"components_my_service_1"}
    docker.compose.down()


def test_docker_compose_start():
    docker.compose.create(["busybox"])
    assert not docker.compose.ps(all=True)[0].state.running
    assert docker.compose.ps() == []
    docker.compose.start(["busybox"])
    assert docker.compose.ps()[0].state.running
    docker.compose.down(timeout=1)


def test_docker_compose_start_stream():
    docker.compose.create(["busybox"])
    assert not docker.compose.ps(all=True)[0].state.running
    assert docker.compose.ps() == []
    logs = list(docker.compose.start(["busybox"], stream_logs=True))
    assert len(logs) >= 2
    full_logs_as_binary = b"".join(log for _, log in logs)
    assert b"Container components_busybox_1  Starting" in full_logs_as_binary
    assert b"Container components_busybox_1  Started" in full_logs_as_binary
    assert docker.compose.ps()[0].state.running
    docker.compose.down(timeout=1)


def test_docker_compose_restart():
    docker.compose.up(["my_service"], detach=True)
    time.sleep(2)

    for container in docker.compose.ps():
        assert (datetime.now(pytz.utc) - container.state.started_at) > timedelta(
            seconds=2
        )

    docker.compose.restart(timeout=1)

    for container in docker.compose.ps():
        assert (datetime.now(pytz.utc) - container.state.started_at) < timedelta(
            seconds=2
        )

    docker.compose.down()


def test_docker_compose_restart_empty_list_of_services():
    docker.compose.up(["my_service"], detach=True)
    time.sleep(2)

    for container in docker.compose.ps():
        assert (datetime.now(pytz.utc) - container.state.started_at) > timedelta(
            seconds=2
        )

    docker.compose.restart([], timeout=1)

    for container in docker.compose.ps():
        assert (datetime.now(pytz.utc) - container.state.started_at) > timedelta(
            seconds=2
        )

    docker.compose.down()


def test_docker_compose_kill():
    docker.compose.up(["my_service", "busybox"], detach=True)

    for container in docker.compose.ps():
        assert container.state.running

    docker.compose.kill("busybox", signal=9)

    assert not docker.container.inspect("components_busybox_1").state.running

    docker.compose.down()


def test_docker_compose_pull():
    try:
        docker.image.remove("busybox")
    except NoSuchImage:
        pass
    try:
        docker.image.remove("alpine")
    except NoSuchImage:
        pass
    docker.compose.pull("busybox")
    docker.compose.pull(["busybox", "alpine"])
    docker.image.inspect(["busybox", "alpine"])

    # pull with quiet should work too
    docker.compose.pull(["busybox", "alpine"], quiet=True)


def test_docker_compose_pull_stream():
    try:
        docker.image.remove("busybox")
    except NoSuchImage:
        pass
    logs = list(docker.compose.pull("busybox", stream_logs=True))
    assert len(logs) >= 3
    logs_as_big_binary = b""
    for log_type, log_value in logs:
        assert log_type in ("stdout", "stderr")
        logs_as_big_binary += log_value
    assert b"busybox Pulled" in logs_as_big_binary
    assert b"Pull complete" in logs_as_big_binary


def test_docker_compose_pull_ignore_pull_failures():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_non_existent_image.yml"
        ]
    )
    try:
        docker.image.remove("ghost")
    except NoSuchImage:
        pass
    docker.compose.pull(["ghost"], ignore_pull_failures=True)


def test_docker_compose_pull_include_deps():
    try:
        docker.image.remove("alpine")
    except NoSuchImage:
        pass
    docker.compose.pull(["busybox-2-electric-boogaloo"], include_deps=True)
    docker.image.inspect(["alpine"])


def test_docker_compose_up_abort_on_container_exit():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_ends_quickly.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up("alpine", abort_on_container_exit=True)
    for container in docker.compose.ps():
        assert not container.state.running
    docker.compose.down()


def test_docker_compose_up_no_attach_services(capfd):
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/compose_logs.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(no_attach_services=["my_service"])

    container_names = [x.name for x in docker.compose.ps()]
    stdout, _ = capfd.readouterr()
    # Checking if we only attach to my_other_service
    expected_output = "Attaching to my_other_service_1, my_other_service_2\n"
    assert expected_output in stdout

    # Checking if the my_service is spun up even if it's not attached
    for name in container_names:
        if "my_service" in name:
            break
    else:
        raise AssertionError("my_service is not spun up as expected")
    docker.compose.down()


def test_passing_env_files(tmp_path: Path):
    compose_env_file = tmp_path / "dodo.env"
    compose_env_file.write_text("SOME_VARIABLE_TO_INSERT=hello\n")
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_ends_quickly.yml"
        ],
        compose_env_file=compose_env_file,
        compose_compatibility=True,
    )
    output = docker.compose.config()

    assert output.services["alpine"].environment["SOME_VARIABLE"] == "hello"


def test_project_directory_env_files(tmp_path: Path):
    makedirs(tmp_path / "some/path")
    makedirs(tmp_path / "some/other/path")
    project_env_file_one = tmp_path / "some/path/one.env"
    project_env_file_two = tmp_path / "some/other/path/two.env"
    project_env_file_one.write_text("TEST=one\n")
    project_env_file_two.write_text("TEST=two\n")
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_project_directory.yml"
        ],
        compose_project_directory=tmp_path,
        compose_compatibility=True,
    )
    output = docker.compose.config()

    assert output.services["alpine_one"].environment["TEST"] == "one"
    assert output.services["alpine_two"].environment["TEST"] == "two"


def test_entrypoint_loaded_in_config():
    assert docker.compose.config().services["dodo"].entrypoint == ["/bin/sh"]


def test_config_complexe_compose():
    """Checking that the pydantic model does its job"""
    compose_file = (
        PROJECT_ROOT / "tests/python_on_whales/components/complexe-compose.yml"
    )
    docker = DockerClient(compose_files=[compose_file], compose_compatibility=True)
    config = docker.compose.config()

    assert config.services["my_service"].build.context == (
        PROJECT_ROOT / "tests/python_on_whales/components/my_service_build"
    )
    assert config.services["my_service"].image == "some_random_image"
    assert config.services["my_service"].command == [
        "ping",
        "-c",
        "2",
        "www.google.com",
    ]

    assert config.services["my_service"].ports[0].published == 5000
    assert config.services["my_service"].ports[0].target == 5000

    assert config.services["my_service"].volumes[0].source == "/tmp"
    assert config.services["my_service"].volumes[0].target == "/tmp"
    assert config.services["my_service"].volumes[1].source == "dodo"
    assert config.services["my_service"].volumes[1].target == "/dodo"

    assert config.services["my_service"].environment == {"DATADOG_HOST": "something"}
    assert config.services["my_service"].deploy.placement.constraints == [
        "node.labels.hello-world == yes"
    ]
    assert config.services["my_service"].deploy.resources.limits.cpus == 2
    assert config.services["my_service"].deploy.resources.limits.memory == 41943040

    assert config.services["my_service"].deploy.resources.reservations.cpus == 1
    assert (
        config.services["my_service"].deploy.resources.reservations.memory == 20971520
    )

    assert config.services["my_service"].deploy.replicas == 4

    assert not config.volumes["dodo"].external


def test_compose_down_volumes():
    compose_file = (
        PROJECT_ROOT / "tests/python_on_whales/components/complexe-compose.yml"
    )
    docker = DockerClient(compose_files=[compose_file], compose_compatibility=True)
    docker.compose.up(
        ["my_service"], detach=True, scales=dict(my_service=1), build=True
    )
    assert docker.volume.exists("components_dodo")
    docker.compose.down()
    assert docker.volume.exists("components_dodo")
    docker.compose.down(volumes=True)
    assert not docker.volume.exists("components_dodo")


@pytest.mark.parametrize("json_file", get_all_jsons("compose"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    config: ComposeConfig = ComposeConfig(**json.loads(json_as_txt))
    if json_file.name == "0.json":
        assert config.services["traefik"].labels["traefik.enable"] == "true"


def test_compose_run_simple():
    result = docker.compose.run("alpine", ["echo", "dodo"], remove=True, tty=False)
    assert result == "dodo"


def test_compose_run_detach():
    container = docker.compose.run("alpine", ["echo", "dodo"], detach=True, tty=False)

    time.sleep(0.1)
    assert not container.state.running
    assert container.logs() == "dodo\n"


def test_docker_compose_run_labels():
    container = docker.compose.run(
        "alpine",
        ["echo", "dodo"],
        labels={"traefik.enable": "false", "hello": "world"},
        detach=True,
        tty=False,
    )

    time.sleep(0.1)
    print(container.config.labels)
    assert container.config.labels.get("traefik.enable") == "false"
    assert container.config.labels.get("hello") == "world"
    docker.compose.down(timeout=1)


def test_compose_version():
    assert "Docker Compose version v2" in docker.compose.version()


def test_compose_logs_simple_use_case():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/compose_logs.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(detach=True)
    # Wait some seconds to let the container to complete the execution of ping
    # and print the statistics
    time.sleep(15)
    full_output = docker.compose.logs()
    assert "error with my_other_service" in full_output
    assert "--- www.google.com ping statistics ---" in full_output
    docker.compose.down(timeout=1)


def test_compose_logs_stream():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/compose_logs.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(detach=True)
    time.sleep(15)
    logs = docker.compose.logs(stream=True)
    logs = list(logs)
    assert any(["error with my_other_service" in log[1].decode() for log in logs])
    assert any(
        ["--- www.google.com ping statistics ---" in log[1].decode() for log in logs]
    )

    docker.compose.down(timeout=1)


def test_compose_logs_follow():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/compose_logs.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(detach=True)

    signal.signal(signal.SIGALRM, mock_KeyboardInterrupt)
    signal.alarm(15)

    start = datetime.now()
    full_output = ""
    try:
        for output_type, current_output in docker.compose.logs(
            follow=True, stream=True
        ):
            full_output += current_output.decode()
        # interrupt the alarm in case the command ends before the timeout
        signal.alarm(0)
    # catch and ignore the exception when the command is interruped by the timeout
    except KeyboardInterrupt:
        pass

    end = datetime.now()

    # 5 seconds because the command can end before the timeout (set to 15 seconds)...
    # but it is enough to verify that the follow flag was working
    # otherwise the logs command should completed in much less than 5 seconds
    assert (end - start).seconds >= 5

    assert "error with my_other_service" in full_output
    assert "--- www.google.com ping statistics ---" in full_output

    docker.compose.down(timeout=1)


@pytest.mark.parametrize("privileged", [True, False])
def test_compose_execute_no_tty(privileged):
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(["busybox"], detach=True)
    time.sleep(2)
    full_output = docker.compose.execute(
        "busybox", ["echo", "dodo"], tty=False, privileged=privileged
    )
    assert full_output == "dodo"
    docker.compose.down(timeout=1)


# We can't test the TTY flag on execute because we can't have a true tty in pytest
# of course tty still works if python-on-whales is executed outside pytest.


def test_compose_execute_detach():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(["busybox"], detach=True)
    t1 = datetime.now()
    output = docker.compose.execute("busybox", ["sleep", "20"], detach=True, tty=False)
    execution_time = datetime.now() - t1
    assert execution_time.seconds < 20
    assert output is None
    docker.compose.down(timeout=1)


def test_compose_execute_envs():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(["busybox"], detach=True)
    output = docker.compose.execute(
        "busybox",
        ["sh", "-c", "echo $VAR1,$VAR2"],
        envs={"VAR1": "hello", "VAR2": "world"},
        tty=False,
    )
    assert output == "hello,world"
    docker.compose.down(timeout=1)


def test_compose_execute_user():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(["busybox"], detach=True)
    output = docker.compose.execute("busybox", ["whoami"], tty=False, user="sync")
    assert output == "sync"
    docker.compose.down(timeout=1)


def test_compose_execute_workdir():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
        ],
        compose_compatibility=True,
    )
    docker.compose.up(["busybox"], detach=True)
    assert (
        docker.compose.execute("busybox", ["pwd"], tty=False, workdir="/tmp") == "/tmp"
    )
    assert (
        docker.compose.execute("busybox", ["pwd"], tty=False, workdir="/proc")
        == "/proc"
    )
    docker.compose.down(timeout=1)


def test_compose_single_profile():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
        ],
        compose_profiles=["my_test_profile"],
        compose_compatibility=True,
    )
    docker.compose.up(detach=True)

    container_names = [x.name for x in docker.compose.ps()]
    assert "components_profile_test_service_1" in container_names

    docker.compose.down(timeout=1)


def test_compose_multiple_profiles():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
        ],
        compose_profiles=["my_test_profile", "my_test_profile2"],
        compose_compatibility=True,
    )
    docker.compose.up(detach=True)

    container_names = [x.name for x in docker.compose.ps()]
    assert "components_profile_test_service_1" in container_names
    assert "components_second_profile_test_service_1" in container_names

    docker.compose.down(timeout=1)


def test_compose_anon_volumes_recreate_not_enabled():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/compose_anon_volumes.yml"
        ],
    )
    docker.compose.up(detach=True)

    volume_name_before_recreate = docker.compose.ps()[0].mounts[0].name

    docker.compose.up(detach=True, force_recreate=True)
    volumes_name_after_recreate = docker.compose.ps()[0].mounts[0].name

    assert volume_name_before_recreate == volumes_name_after_recreate

    docker.compose.down(timeout=1)


def test_compose_anon_volumes_recreate_enabled():
    docker = DockerClient(
        compose_files=[
            PROJECT_ROOT / "tests/python_on_whales/components/compose_anon_volumes.yml"
        ],
    )
    docker.compose.up(detach=True)

    volume_name_before_recreate = docker.compose.ps()[0].mounts[0].name

    docker.compose.up(detach=True, force_recreate=True, renew_anon_volumes=True)
    volumes_name_after_recreate = docker.compose.ps()[0].mounts[0].name

    assert volume_name_before_recreate != volumes_name_after_recreate

    docker.compose.down(timeout=1)


def test_compose_port():
    d = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_non_existent_image.yml"
        ]
    )
    service = "busybox"
    d.compose.up(services=[service], detach=True)

    expected_tcp_host, expected_tcp_port, expected_udp_host, expected_udp_port = (
        None,
        None,
        None,
        None,
    )
    container = next(filter(lambda x: service in x.name, d.compose.ps()))
    tcp_cfg = container.network_settings.ports["3000/tcp"][0]
    expected_tcp_host, expected_tcp_port = tcp_cfg["HostIp"], int(tcp_cfg["HostPort"])
    udp_cfg = container.network_settings.ports["4000/udp"][0]
    expected_udp_host, expected_udp_port = udp_cfg["HostIp"], int(udp_cfg["HostPort"])

    tcp_host, tcp_port = d.compose.port(service, "3000", protocol="tcp")
    assert expected_tcp_host == tcp_host
    assert expected_tcp_port == tcp_port

    udp_host, udp_port = d.compose.port(service, "4000", protocol="udp")
    assert expected_udp_host == udp_host
    assert expected_udp_port == udp_port

    with pytest.raises(DockerException) as err:
        d.compose.port(service, "4000", protocol="tcp")
    assert "no port 4000/tcp for container components-busybox-1" in str(err)

    with pytest.raises(DockerException) as err:
        d.compose.port(service, "1111")
    assert "no port 1111/tcp for container components-busybox-1" in str(err)

    with pytest.raises(ValueError) as err:
        d.compose.port("", "123")
    assert "Service cannot be empty" in str(err)

    with pytest.raises(ValueError) as err:
        d.compose.port(service, "")
    assert "Private port cannot be empty" in str(err)

    d.compose.down(timeout=1)


def test_compose_ls_project_multiple_statuses():
    d = DockerClient(
        compose_files=[
            PROJECT_ROOT
            / "tests/python_on_whales/components/dummy_compose_ends_quickly.yml",
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml",
        ],
        compose_compatibility=True,
        compose_project_name="test_compose_ls",
    )
    d.compose.up(["alpine", "dodo"], detach=True)
    time.sleep(2)

    projects = d.compose.ls(all=True)
    project = [
        proj
        for proj in projects
        if proj.name == d.compose.client_config.compose_project_name
    ][0]

    assert project.running == 1
    assert project.exited == 1
    assert project.paused == 0
    if project.config_files:
        assert sorted(project.config_files) == sorted(d.client_config.compose_files)

    d.compose.down(timeout=1)


def check_number_of_running_containers(
    docker_client, expected, countable_container_ids
):
    """
    Check that we have the expected number of running containers out of the specified ones,
    Running containers that do not have their id in the list won't be counted.
    :param docker_client: docker client to use
    :param expected: the number of expected running containers
    :param countable_container_ids: a list of container ids
    :return: None
    """
    containers = docker_client.ps()
    container_ids = {container.id for container in containers}
    assert len(set(countable_container_ids).intersection(container_ids)) == expected


def test_docker_compose_up_remove_orphans():
    compose_file = tempfile.mktemp(
        prefix="test_docker_compose_up_remove_orphans_", suffix=".yml"
    )
    compose_file = Path(compose_file)
    docker = DockerClient(
        compose_files=[compose_file],
        compose_compatibility=True,
    )
    base_cfg = """version: "3.7"
services:
  busybox1:
    image: busybox:latest
    command: sleep infinity
"""
    service_to_remove = """  busybox2:
    image: busybox:latest
    command: sleep infinity
"""

    # writing the docker compose file with 2 services configured
    compose_file.write_text(base_cfg + service_to_remove)

    docker.compose.up(detach=True)
    compose_containers = docker.compose.ps()
    assert len(compose_containers) == 2
    compose_container_ids = {container.id for container in compose_containers}

    # updating the docker compose file to have only 1 service configured
    compose_file.write_text(base_cfg)

    docker.compose.up(detach=True)
    # both containers running
    check_number_of_running_containers(docker, 2, compose_container_ids)

    # calling with remove_orphans flag
    docker.compose.up(detach=True, remove_orphans=True)
    # orphan container (of the removed service) was stopped
    check_number_of_running_containers(docker, 1, compose_container_ids)

    docker.compose.down(timeout=1)
    check_number_of_running_containers(docker, 0, compose_container_ids)
    remove(compose_file)


def test_docker_compose_run_build():
    docker.compose.run("my_service", build=True, detach=True, tty=False)
    docker.compose.stop()
    docker.compose.rm()
    assert (
        docker.compose.config(return_json=True)["services"]["my_service"]["image"]
        == docker.image.list("some_random_image")[0].repo_tags[0].split(":latest")[0]
    )
    docker.image.remove("some_random_image", force=True)


def test_build_args():
    compose_file = (
        PROJECT_ROOT / "tests/python_on_whales/components/test-build-args.yml"
    )
    docker = DockerClient(compose_files=[compose_file])
    config = docker.compose.config()

    assert (
        config.services["my_service"].build.context
        == (compose_file.parent / "my_service_build").absolute()
    )
    assert config.services["my_service"].build.dockerfile == Path(
        "docker/somefile.dockerfile"
    )
    assert config.services["my_service"].build.args == {
        "python_version": "3.78",
        "python_version_1": "3.78",
    }
    assert config.services["my_service"].build.labels == {
        "com.example.description": "Accounting webapp",
        "com.example.department": "Finance",
    }
    assert config.services["my_service"].image == "some_random_image"
    assert config.services["my_service"].command == [
        "ping",
        "-c",
        "7",
        "www.google.com",
    ]

    assert config.services["my_service"].ports[0].published == 5000
    assert config.services["my_service"].ports[0].target == 5000

    assert config.services["my_service"].volumes[0].source == "/tmp"
    assert config.services["my_service"].volumes[0].target == "/tmp"
    assert config.services["my_service"].volumes[1].source == "dodo"
    assert config.services["my_service"].volumes[1].target == "/dodo"

    assert config.services["my_service"].environment == {"DATADOG_HOST": "something"}
