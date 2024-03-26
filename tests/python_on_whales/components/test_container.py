import json
import os
import signal
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Union
from unittest.mock import Mock, patch

import pytest

import python_on_whales
from python_on_whales import DockerClient, Image, docker
from python_on_whales.components.container.cli_wrapper import ContainerStats
from python_on_whales.components.container.models import (
    ContainerInspectResult,
    ContainerState,
)
from python_on_whales.exceptions import DockerException, NoSuchContainer
from python_on_whales.test_utils import get_all_jsons, random_name


def build_image(ctr_client: DockerClient, python_code: str) -> Image:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        (tmpdir / "file.py").write_text(python_code)
        (tmpdir / "Dockerfile").write_text(
            f"""
FROM python:{sys.version_info[0]}.{sys.version_info[1]}
COPY file.py /file.py
CMD python /file.py
        """
        )
        return ctr_client.build(tmpdir, tags="some_image", load=True)


@pytest.mark.parametrize("json_file", get_all_jsons("containers"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ContainerInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_command(ctr_client: DockerClient):
    output = ctr_client.run("hello-world", remove=True)
    assert "Hello from Docker!" in output


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_mistake_on_run(ctr_client: DockerClient):
    with pytest.raises(TypeError) as err:
        ctr_client.run("ubuntu", "ls")
    assert "docker.run('ubuntu', ['ls'], ...)" in str(err)
    ctr_client.run("ubuntu", ["ls"], remove=True)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_command_create_start(ctr_client: DockerClient):
    output = ctr_client.container.create("hello-world", remove=True).start(attach=True)
    assert "Hello from Docker!" in output


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_stream(ctr_client: DockerClient):
    output = ctr_client.run("hello-world", remove=True, stream=True)

    assert ("stdout", b"Hello from Docker!\n") in list(output)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_stream_create_start(ctr_client: DockerClient):
    container = ctr_client.container.create("hello-world", remove=True)
    output = container.start(attach=True, stream=True)
    assert ("stdout", b"Hello from Docker!\n") in list(output)


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_same_output_run_create_start(ctr_client: DockerClient):
    python_code = """
import sys
sys.stdout.write("everything is fine\\n\\nhello world")
sys.stderr.write("Something is wrong!")
    """
    image = build_image(ctr_client, python_code)
    output_run = ctr_client.run(image, remove=True)
    output_create = ctr_client.container.create(image, remove=True).start(attach=True)
    assert output_run == output_create


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_same_stream_run_create_start(ctr_client: DockerClient):
    python_code = """
import sys
sys.stdout.write("everything is fine\\n\\nhello world")
sys.stderr.write("Something is wrong!")
    """
    image = build_image(ctr_client, python_code)
    output_run = set(ctr_client.run(image, remove=True, stream=True))
    container = ctr_client.container.create(image, remove=True)
    output_create = set(container.start(attach=True, stream=True))
    assert output_run == output_create


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_exact_output(ctr_client: DockerClient):
    try:
        ctr_client.image.remove("busybox")
    except DockerException:
        pass
    assert ctr_client.run("busybox", ["echo", "dodo"], remove=True) == "dodo"


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_fails_correctly(ctr_client: DockerClient):
    python_code = """
import sys
sys.stdout.write("everything is fine")
sys.stderr.write("Something is wrong!")
sys.exit(1)
"""
    image = build_image(ctr_client, python_code)
    with image:
        with pytest.raises(DockerException) as err:
            for _ in ctr_client.run(image, stream=True, remove=True):
                pass
        assert "Something is wrong!" in str(err.value)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_container_repr(ctr_client: DockerClient):
    with ctr_client.run(
        "ubuntu",
        ["sleep", "infinity"],
        remove=True,
        detach=True,
        stop_timeout=1,
    ) as container:
        assert container.id[:12] in repr(ctr_client.container.list())


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_run_with_random_port(ctr_client: DockerClient):
    with ctr_client.run(
        "ubuntu",
        ["sleep", "infinity"],
        publish=[(90,)],
        remove=True,
        detach=True,
        stop_timeout=1,
    ) as container:
        assert container.network_settings.ports["90/tcp"][0]["HostPort"] is not None
        assert container.id[:12] in repr(ctr_client.container.list())


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_create_with_random_ports(ctr_client: DockerClient):
    with ctr_client.container.create(
        "ubuntu", ["sleep", "infinity"], publish=[(90,)], stop_timeout=1
    ) as container:
        container.start()
        assert container.network_settings.ports["90/tcp"][0]["HostPort"] is not None


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_create_with_cgroupns(ctr_client: DockerClient):
    with ctr_client.container.run(
        "ubuntu", ["sleep", "infinity"], cgroupns="host", detach=True, stop_timeout=1
    ) as container:
        assert container.host_config.cgroupns_mode == "host"


@pytest.mark.parametrize("systemd_mode", [True, False, "always"])
@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container", Mock())
def test_mock_create_with_systemd_mode(
    run_mock: Mock, systemd_mode: Union[bool, Literal["always"]]
):
    docker.container.create(
        "ubuntu", ["sleep", "infinity"], systemd=systemd_mode, pull="never"
    )
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd
        + [
            # fmt: off
            "create",
            "--pull", "never",
            "--systemd", systemd_mode,
            "ubuntu",
            "sleep", "infinity",
            # fmt: on
        ]
    )


def test_create_with_systemd_mode(podman_client: DockerClient):
    with podman_client.container.run(
        "ubuntu", ["sleep", "infinity"], systemd="always", detach=True, stop_timeout=1
    ) as container:
        assert container.config.systemd_mode is True


def test_create_in_pod(podman_client: DockerClient):
    pod_name = random_name()
    with podman_client.pod.create(pod_name) as pod:
        container = podman_client.container.create("ubuntu", pod=pod_name)
        assert container.pod == pod.id
    assert not container.exists()


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_fails_correctly_create_start(ctr_client: DockerClient):
    python_code = """
import sys
sys.stdout.write("everything is fine")
sys.stderr.write("Something is wrong!")
sys.exit(1)
"""
    image = build_image(ctr_client, python_code)
    with image:
        container = ctr_client.container.create(image, remove=True)
        with pytest.raises(DockerException) as err:
            for _ in container.start(attach=True, stream=True):
                pass
        assert "Something is wrong!" in str(err.value)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_remove_on_exit(ctr_client: DockerClient):
    output = ctr_client.run("hello-world", remove=True)
    assert "Hello from Docker!" in output


@pytest.mark.parametrize(
    "ctr_client",
    [
        "docker",
        pytest.param(
            "podman",
            marks=pytest.mark.xfail(
                reason="Cgroup control not available with rootless podman on cgroups v1"
            ),
        ),
    ],
    indirect=True,
)
def test_cpus(ctr_client: DockerClient):
    output = ctr_client.run("hello-world", cpus=1.5, remove=True)
    assert "Hello from Docker!" in output


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_run_volumes(ctr_client: DockerClient):
    volume_name = random_name()
    ctr_client.run(
        "busybox",
        ["touch", "/some/path/dodo"],
        volumes=[(volume_name, "/some/path")],
        remove=True,
    )
    ctr_client.volume.remove(volume_name)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_remove_manually(ctr_client: DockerClient):
    container = ctr_client.run("hello-world", detach=True)
    time.sleep(0.3)
    assert container in ctr_client.container.list(all=True)
    ctr_client.container.remove(container)
    assert container not in ctr_client.container.list(all=True)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_logs(ctr_client: DockerClient):
    with ctr_client.run("busybox:1", ["echo", "dodo"], detach=True) as c:
        time.sleep(0.3)
        output = ctr_client.container.logs(c)
        assert output == "dodo\n"


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_logs_stderr(ctr_client: DockerClient):
    with ctr_client.run("busybox:1", ["sh", "-c", ">&2 echo dodo"], detach=True) as c:
        time.sleep(0.3)
        output = ctr_client.container.logs(c)
        assert output == "dodo\n"


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_logs_do_not_follow(ctr_client: DockerClient):
    with ctr_client.run(
        "busybox:1", ["sh", "-c", "sleep 3 && echo dodo"], detach=True
    ) as c:
        output = ctr_client.container.logs(c, follow=False)
        assert output == ""


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_logs_follow(ctr_client: DockerClient):
    with ctr_client.run(
        "busybox:1", ["sh", "-c", "sleep 3 && echo dodo"], detach=True
    ) as c:
        output = ctr_client.container.logs(c, follow=True)
        assert output == "dodo\n"


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_logs_stream(ctr_client: DockerClient):
    with ctr_client.run("busybox:1", ["echo", "dodo"], detach=True) as c:
        time.sleep(0.3)
        output = list(ctr_client.container.logs(c, stream=True))
        assert output == [("stdout", b"dodo\n")]


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_logs_stream_stderr(ctr_client: DockerClient):
    with ctr_client.run("busybox:1", ["sh", "-c", ">&2 echo dodo"], detach=True) as c:
        time.sleep(0.3)
        output = list(ctr_client.container.logs(c, stream=True))
        assert output == [("stderr", b"dodo\n")]


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_logs_stream_stdout_and_stderr(ctr_client: DockerClient):
    with ctr_client.run(
        "busybox:1", ["sh", "-c", ">&2 echo dodo && echo dudu"], detach=True
    ) as c:
        time.sleep(0.3)
        output = list(ctr_client.container.logs(c, stream=True))

        # the order of stderr and stdout is not guaranteed.
        assert set(output) == {("stderr", b"dodo\n"), ("stdout", b"dudu\n")}


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_simple_logs_stream_wait(ctr_client: DockerClient):
    with ctr_client.run(
        "busybox:1", ["sh", "-c", "sleep 3 && echo dodo"], detach=True
    ) as c:
        time.sleep(0.3)
        output = list(ctr_client.container.logs(c, follow=True, stream=True))
        assert output == [("stdout", b"dodo\n")]


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_rename(ctr_client: DockerClient):
    name = random_name()
    new_name = random_name()
    assert name != new_name
    container = ctr_client.container.run("hello-world", name=name, detach=True)
    ctr_client.container.rename(container, new_name)
    container.reload()

    assert container.name == new_name
    ctr_client.container.remove(container)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_name(ctr_client: DockerClient):
    name = random_name()
    container = ctr_client.container.run("hello-world", name=name, detach=True)
    assert container.name == name
    ctr_client.container.remove(container)


json_state = """
{
    "Status": "running",
    "Running": true,
    "Paused": false,
    "Restarting": false,
    "OOMKilled": false,
    "Dead": false,
    "Pid": 1462,
    "ExitCode": 0,
    "Error": "",
    "StartedAt": "2020-09-02T20:14:54.3151689Z",
    "FinishedAt": "2020-09-02T22:14:50.4625972+02:00"
}
"""


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_container_state(ctr_client: DockerClient):
    a = ContainerState(**json.loads(json_state))

    assert a.status == "running"
    assert a.running
    assert a.exit_code == 0
    assert a.finished_at == datetime(
        2020, 9, 2, 22, 14, 50, 462597, tzinfo=timezone(timedelta(hours=2))
    )


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_restart(ctr_client: DockerClient):
    cmd = ["sleep", "infinity"]
    containers = [ctr_client.run("busybox:1", cmd, detach=True) for _ in range(3)]
    ctr_client.kill(containers)

    ctr_client.restart(containers)
    for container in containers:
        assert container.state.running


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_execute(ctr_client: DockerClient):
    my_container = ctr_client.run(
        "busybox:1", ["sleep", "infinity"], detach=True, remove=True
    )
    exec_result = ctr_client.execute(my_container, ["echo", "dodo"])
    assert exec_result == "dodo"
    ctr_client.kill(my_container)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_execute_simple_mistake(ctr_client: DockerClient):
    with ctr_client.run(
        "busybox:1", ["sleep", "infinity"], detach=True, remove=True
    ) as my_container:
        with pytest.raises(TypeError) as err:
            ctr_client.execute(my_container, "echo dodo")
        assert f"docker.execute('{my_container.name}', ['echo', 'dodo'], ...)" in str(
            err
        )


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_execute_stream(ctr_client: DockerClient):
    my_container = ctr_client.run(
        "busybox:1", ["sleep", "infinity"], detach=True, remove=True
    )
    exec_result = list(
        ctr_client.execute(my_container, ["sh", "-c", ">&2 echo dodo"], stream=True)
    )
    assert exec_result == [("stderr", b"dodo\n")]
    ctr_client.kill(my_container)


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_diff(ctr_client: DockerClient):
    my_container = ctr_client.run(
        "busybox:1", ["sleep", "infinity"], detach=True, remove=True
    )

    ctr_client.execute(my_container, ["mkdir", "/some_path"])
    ctr_client.execute(my_container, ["touch", "/some_file"])
    ctr_client.execute(my_container, ["rm", "-rf", "/tmp"])

    diff = ctr_client.diff(my_container)
    assert diff == {"/some_path": "A", "/some_file": "A", "/tmp": "D"}
    ctr_client.kill(my_container)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_methods(ctr_client: DockerClient):
    my_container = ctr_client.run("busybox:1", ["sleep", "infinity"], detach=True)
    my_container.kill()
    assert not my_container.state.running
    my_container.remove()


@pytest.mark.parametrize(
    "ctr_client",
    [
        "docker",
        pytest.param(
            "podman",
            marks=pytest.mark.xfail(
                reason="container sometimes fails to exit with podman", strict=False
            ),
        ),
    ],
    indirect=True,
)
def test_kill_signal(ctr_client: DockerClient):
    my_container = ctr_client.run(
        "busybox:1", ["sleep", "infinity"], init=True, detach=True
    )
    my_container.kill(signal=signal.SIGINT)
    assert not my_container.state.running
    assert my_container.state.exit_code == 130
    my_container.remove()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_context_manager(ctr_client: DockerClient):
    container_name = random_name()
    with pytest.raises(ArithmeticError):
        with ctr_client.run(
            "busybox:1", ["sleep", "infinity"], detach=True, name=container_name
        ):
            raise ArithmeticError

    assert container_name not in [x.name for x in ctr_client.container.list(all=True)]


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_context_manager_with_create(ctr_client: DockerClient):
    container_name = random_name()
    with pytest.raises(ArithmeticError):
        with ctr_client.container.create(
            "busybox:1", ["sleep", "infinity"], name=container_name
        ) as c:
            assert isinstance(c, python_on_whales.Container)
            raise ArithmeticError

    assert container_name not in [x.name for x in ctr_client.container.list(all=True)]


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_filters(ctr_client: DockerClient):
    random_label_value = random_name()

    containers_with_labels = []

    for _ in range(3):
        containers_with_labels.append(
            ctr_client.run(
                "busybox",
                ["sleep", "infinity"],
                remove=True,
                detach=True,
                labels=dict(dodo=random_label_value),
            )
        )

    containers_with_wrong_labels = []
    for _ in range(3):
        containers_with_wrong_labels.append(
            ctr_client.run(
                "busybox",
                ["sleep", "infinity"],
                remove=True,
                detach=True,
                labels=dict(dodo="something"),
            )
        )

    expected_containers_with_labels = ctr_client.container.list(
        filters=dict(label=f"dodo={random_label_value}")
    )

    assert set(expected_containers_with_labels) == set(containers_with_labels)

    for container in containers_with_labels + containers_with_wrong_labels:
        container.kill()


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_wait_single_container(ctr_client: DockerClient):
    cont_1 = ctr_client.run("busybox", ["sh", "-c", "sleep 2 && exit 8"], detach=True)
    with cont_1:
        exit_code = ctr_client.wait(cont_1)

    assert exit_code == 8


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_wait_single_container_already_finished(ctr_client: DockerClient):
    cont_1 = ctr_client.run("busybox", ["sh", "-c", "exit 8"], detach=True)
    first_exit_code = ctr_client.wait(cont_1)
    second_exit_code = ctr_client.wait(cont_1)

    assert first_exit_code == second_exit_code == 8


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_wait_multiple_container(ctr_client: DockerClient):
    cont_1 = ctr_client.run("busybox", ["sh", "-c", "sleep 2 && exit 8"], detach=True)
    cont_2 = ctr_client.run("busybox", ["sh", "-c", "sleep 2 && exit 10"], detach=True)

    with cont_1, cont_2:
        exit_codes = ctr_client.wait([cont_1, cont_2])

    assert exit_codes == [8, 10]


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_wait_multiple_container_random_exit_order(ctr_client: DockerClient):
    cont_1 = ctr_client.run("busybox", ["sh", "-c", "sleep 4 && exit 8"], detach=True)
    cont_2 = ctr_client.run("busybox", ["sh", "-c", "sleep 2 && exit 10"], detach=True)

    with cont_1, cont_2:
        exit_codes = ctr_client.wait([cont_1, cont_2])

    assert exit_codes == [8, 10]


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_pause_unpause(ctr_client: DockerClient):
    container = ctr_client.run(
        "busybox", ["ping", "www.google.com"], detach=True, remove=True
    )

    with container:
        assert container.state.running
        container.pause()
        assert container.state.paused
        container.unpause()
        assert not container.state.paused
        assert container.state.running


@pytest.mark.parametrize("json_file", get_all_jsons("stats"))
def test_load_stats_json(json_file):
    json_as_txt = json_file.read_text()
    stats = ContainerStats(json.loads(json_as_txt))
    assert stats.memory_used > 100


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_stats_all(ctr_client: DockerClient):
    with ctr_client.run(
        "busybox", ["sleep", "infinity"], detach=True, stop_timeout=1
    ) as container:
        for stat in ctr_client.stats():
            if stat.container_id == container.id:
                break
        assert stat.container_name == container.name
        assert stat.cpu_percentage <= 5
        assert stat.memory_used <= 100_000_000


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_stats_container(ctr_client: DockerClient):
    with ctr_client.run("busybox", ["sleep", "infinity"], detach=True) as container:
        with ctr_client.run("busybox", ["sleep", "infinity"], detach=True):
            stats = ctr_client.stats(containers=[container.id])
            assert len(stats) == 1
            assert stats[0].container_name == container.name


@patch("python_on_whales.components.container.cli_wrapper.run")
def test_stats_cli_default(run_mock: Mock):
    docker.container.stats()
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd
        + [
            "container",
            "stats",
            "--format",
            "{{json .}}",
            "--no-stream",
            "--no-trunc",
        ]
    )


@patch("python_on_whales.components.container.cli_wrapper.run")
def test_stats_cli_container(run_mock: Mock):
    test_containers = ["dummy_container_0", "dummy_container_1"]
    docker.container.stats(containers=test_containers)
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd
        + [
            "container",
            "stats",
            "--format",
            "{{json .}}",
            "--no-stream",
            "--no-trunc",
        ]
        + test_containers
    )


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_stats_cli_empty_selection(ctr_client: DockerClient):
    assert ctr_client.container.stats(containers=[]) == []


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_remove_anonymous_volume_too(ctr_client: DockerClient):
    container = ctr_client.run("postgres:9.6.20-alpine", detach=True)

    volume_id = container.mounts[0].name
    volume = ctr_client.volume.inspect(volume_id)

    with container:
        pass

    assert volume not in ctr_client.volume.list()
    assert container not in ctr_client.ps(all=True)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_remove_nothing(ctr_client: DockerClient):
    ctr_client.container.remove([])


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_stop_nothing(ctr_client: DockerClient):
    ctr_client.container.stop([])


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_kill_nothing(ctr_client: DockerClient):
    with ctr_client.run("ubuntu", ["sleep", "infinity"], detach=True, remove=True):
        set_of_containers = set(ctr_client.ps())
        ctr_client.container.kill([])
        assert set_of_containers == set(ctr_client.ps())


@patch("python_on_whales.components.container.cli_wrapper.run")
def test_start_detach_keys(run_mock: Mock):
    docker.start("ctr_name", detach_keys="a,b")
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd
        + ["container", "start", "--detach-keys", "a,b", "ctr_name"]
    )


def test_run_with_env_host(podman_client: DockerClient):
    try:
        os.environ["POW_TEST_FOO"] = "foo"
        os.environ["POW_TEST_BAR"] = "bar"
        with podman_client.run(
            "ubuntu",
            ["sleep", "infinity"],
            env_host=True,
            envs={"POW_TEST_BAR": "override"},
            detach=True,
        ) as c:
            foo_env = c.execute(["bash", "-c", "echo $POW_TEST_FOO"])
            bar_env = c.execute(["bash", "-c", "echo $POW_TEST_BAR"])
        assert foo_env == "foo"
        assert bar_env == "override"
    finally:
        os.environ.pop("POW_TEST_FOO")
        os.environ.pop("POW_TEST_BAR")


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_exec_env(ctr_client: DockerClient):
    with ctr_client.run("ubuntu", ["sleep", "infinity"], detach=True, remove=True) as c:
        result = c.execute(["bash", "-c", "echo $DODO"], envs={"DODO": "dada"})

    assert result == "dada"


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_exec_env_file(ctr_client: DockerClient, tmp_path: Path):
    env_file = tmp_path / "variables.env"
    env_file.write_text("DODO=dada\n")

    with ctr_client.run("ubuntu", ["sleep", "infinity"], detach=True, remove=True) as c:
        result = c.execute(["bash", "-c", "echo $DODO"], env_files=[env_file])
    assert result == "dada"


@patch("python_on_whales.components.container.cli_wrapper.run")
def test_exec_detach_keys(run_mock: Mock):
    docker.execute("ctr_name", ["cmd"], detach_keys="a,b")
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd
        + ["exec", "--detach-keys", "a,b", "ctr_name", "cmd"],
        tty=False,
    )


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_export_file(ctr_client: DockerClient, tmp_path: Path):
    dest = tmp_path / "dodo.tar"
    with ctr_client.run(
        "busybox", ["sleep", "infinity"], detach=True, remove=True
    ) as c:
        c.export(dest)

    assert dest.exists()
    assert dest.stat().st_size > 10_000


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_exec_privilged_flag(ctr_client: DockerClient, mocker):
    fake_completed_process = mocker.MagicMock()
    fake_completed_process.returncode = 0

    patched_run = mocker.patch("subprocess.run")
    patched_run.return_value = fake_completed_process
    ctr_client.execute("my_container", ["some_command"], privileged=True)

    assert patched_run.call_args[0][0][1:] == [
        "exec",
        "--privileged",
        "my_container",
        "some_command",
    ]


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_exec_change_user(ctr_client: DockerClient):
    with ctr_client.run("ubuntu", ["sleep", "infinity"], detach=True, remove=True) as c:
        c.execute(["useradd", "-ms", "/bin/bash", "newuser"])
        assert c.execute(["whoami"], user="newuser") == "newuser"


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_exec_change_directory(ctr_client: DockerClient):
    with ctr_client.run("ubuntu", ["sleep", "infinity"], detach=True, remove=True) as c:
        assert c.execute(["pwd"], workdir="/tmp") == "/tmp"
        assert c.execute(["pwd"], workdir="/etc") == "/etc"
        assert c.execute(["pwd"], workdir="/usr/lib") == "/usr/lib"


@pytest.mark.parametrize(
    "method",
    [
        "attach",
        "commit",
        "diff",
        "inspect",
        "kill",
        "logs",
        "pause",
        "remove",
        "restart",
        "start",
        "stop",
        "unpause",
        "wait",
    ],
)
@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_functions_nosuchcontainer(ctr_client: DockerClient, method: str):
    if ctr_client.client_config.client_type == "podman" and method in [
        "diff",
        "pause",
        "unpause",
    ]:
        pytest.xfail()
    with pytest.raises(NoSuchContainer):
        getattr(ctr_client.container, method)("DOODODGOIHURHURI")


@pytest.mark.parametrize(
    "ctr_client",
    ["docker", pytest.param("podman", marks=pytest.mark.xfail)],
    indirect=True,
)
def test_copy_nosuchcontainer(ctr_client: DockerClient):
    with pytest.raises(NoSuchContainer):
        ctr_client.container.copy(
            ("dodueizbgueirzhgueoz", "/dududada"), "/tmp/dudufeoz"
        )


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_execute_nosuchcontainer(ctr_client: DockerClient):
    with pytest.raises(NoSuchContainer):
        ctr_client.container.execute("dodueizbgueirzhgueoz", ["echo", "dudu"])


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_export_nosuchcontainer(ctr_client: DockerClient, tmp_path: Path):
    dest = tmp_path / "dodo.tar"
    with pytest.raises(NoSuchContainer):
        ctr_client.container.export("some_random_container_that_does_not_exists", dest)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_rename_nosuchcontainer(ctr_client: DockerClient):
    with pytest.raises(NoSuchContainer):
        ctr_client.container.rename("dodueizbgueirzhgueoz", "new_name")


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_update_nosuchcontainer(ctr_client: DockerClient):
    with pytest.raises(NoSuchContainer):
        ctr_client.container.update("grueighuri", cpus=1)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_prune(ctr_client: DockerClient):
    for container in ctr_client.container.list(filters={"name": "test-container"}):
        ctr_client.container.remove(container, force=True)
    container = ctr_client.container.create("busybox")
    assert container in ctr_client.container.list(all=True)

    # container not pruned because it is not old enough
    ctr_client.container.prune(filters={"until": "100h"})
    assert container in ctr_client.container.list(all=True)

    # container not pruned because it is does not have label "dne"
    ctr_client.container.prune(filters={"label": "dne"})
    assert container in ctr_client.container.list(all=True)

    # container not pruned because it is not old enough and does not have label "dne"
    ctr_client.container.prune(filters={"until": "100h", "label": "dne"})
    assert container in ctr_client.container.list(all=True)

    # container pruned
    ctr_client.container.prune()
    assert container not in ctr_client.container.list(all=True)


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_prune_streaming(ctr_client: DockerClient):
    for container in ctr_client.container.list(filters={"name": "test-container"}):
        ctr_client.container.remove(container, force=True)
    container = ctr_client.container.create("busybox")
    assert container in ctr_client.container.list(all=True)

    # container not pruned because it is not old enough
    # podman does not provide logs when not pruned
    logs = list(ctr_client.container.prune(filters={"until": "100h"}, stream_logs=True))
    assert container in ctr_client.container.list(all=True)

    if ctr_client.client_config.client_type == "docker":
        assert len(logs) >= 1
    logs_as_big_binary = b""
    for log_type, log_value in logs:
        if ctr_client.client_config.client_type == "docker":
            assert log_type in ("stdout", "stderr")
            logs_as_big_binary += log_value

    if ctr_client.client_config.client_type == "docker":
        assert b"Total reclaimed space:" in logs_as_big_binary

    # container not pruned because it is does not have label "dne"
    # podman does not provide logs when not pruned
    logs = list(ctr_client.container.prune(filters={"label": "dne"}, stream_logs=True))
    assert container in ctr_client.container.list(all=True)

    if ctr_client.client_config.client_type == "docker":
        assert len(logs) >= 1
    logs_as_big_binary = b""
    for log_type, log_value in logs:
        if ctr_client.client_config.client_type == "docker":
            assert log_type in ("stdout", "stderr")
            logs_as_big_binary += log_value

    if ctr_client.client_config.client_type == "docker":
        assert b"Total reclaimed space:" in logs_as_big_binary

    # container not pruned because it is not old enough and does not have label "dne"
    # podman does not provide logs when not pruned
    logs = list(
        ctr_client.container.prune(
            filters={"until": "100h", "label": "dne"}, stream_logs=True
        )
    )
    assert container in ctr_client.container.list(all=True)

    if ctr_client.client_config.client_type == "docker":
        assert len(logs) >= 1
    logs_as_big_binary = b""
    for log_type, log_value in logs:
        if ctr_client.client_config.client_type == "docker":
            assert log_type in ("stdout", "stderr")
        logs_as_big_binary += log_value

    if ctr_client.client_config.client_type == "docker":
        assert b"Total reclaimed space:" in logs_as_big_binary

    # container pruned
    # podman does provide logs when pruned
    logs = list(ctr_client.container.prune(stream_logs=True))
    assert container not in ctr_client.container.list(all=True)

    if ctr_client.client_config.client_type == "docker":
        len(logs) >= 3

    if ctr_client.client_config.client_type == "podman":
        len(logs) >= 1

    logs_as_big_binary = b""
    for log_type, log_value in logs:
        if ctr_client.client_config.client_type == "docker":
            assert log_type in ("stdout", "stderr")
        logs_as_big_binary += log_value

    if ctr_client.client_config.client_type == "docker":
        assert b"Total reclaimed space:" in logs_as_big_binary


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_run_detached_interactive(ctr_client: DockerClient):
    with ctr_client.run("ubuntu", interactive=True, detach=True, tty=False) as c:
        c.execute(["true"])


@patch("python_on_whales.components.container.cli_wrapper.ContainerCLI.inspect")
@patch("python_on_whales.components.container.cli_wrapper.run")
def test_attach_default(run_mock: Mock, inspect_mock: Mock):
    test_container_name = "test_dummy_container"

    docker.attach(test_container_name)

    inspect_mock.assert_called_once_with(test_container_name)
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd
        + ["attach", "--sig-proxy", test_container_name],
        tty=True,
    )


@patch("python_on_whales.components.container.cli_wrapper.ContainerCLI.inspect")
@patch("python_on_whales.components.container.cli_wrapper.run")
def test_attach_detach_keys_argument(run_mock: Mock, inspect_mock: Mock):
    test_container_name = "test_dummy_container"
    test_detach_key = "dummy"

    docker.attach(test_container_name, detach_keys=test_detach_key)

    inspect_mock.assert_called_once_with(test_container_name)
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd
        + [
            "attach",
            "--detach-keys",
            test_detach_key,
            "--sig-proxy",
            test_container_name,
        ],
        tty=True,
    )


@patch("python_on_whales.components.container.cli_wrapper.ContainerCLI.inspect")
@patch("python_on_whales.components.container.cli_wrapper.run")
def test_attach_no_stdin_argument(run_mock: Mock, inspect_mock: Mock):
    test_container_name = "test_dummy_container"

    docker.attach(test_container_name, stdin=False)

    inspect_mock.assert_called_once_with(test_container_name)
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd
        + ["attach", "--no-stdin", "--sig-proxy", test_container_name],
        tty=True,
    )


@patch("python_on_whales.components.container.cli_wrapper.ContainerCLI.inspect")
@patch("python_on_whales.components.container.cli_wrapper.run")
def test_attach_sig_proxy_argument(run_mock: Mock, inspect_mock: Mock):
    test_container_name = "test_dummy_container"

    docker.attach(test_container_name, sig_proxy=False)

    inspect_mock.assert_called_once_with(test_container_name)
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd + ["attach", test_container_name], tty=True
    )


@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container")
@patch("python_on_whales.components.image.cli_wrapper.ImageCLI")
def test_create_default_pull(image_mock: Mock, _: Mock, run_mock: Mock):
    image_cli_mock = Mock()
    image_mock.return_value = image_cli_mock

    test_image_name = "test_dummy_image"

    docker.create(test_image_name)

    image_cli_mock._pull_if_necessary.assert_called_once_with(test_image_name)
    image_cli_mock.pull.assert_not_called()
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd + ["create", test_image_name]
    )


@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container")
@patch("python_on_whales.components.image.cli_wrapper.ImageCLI")
def test_create_missing_pull(image_mock: Mock, _: Mock, run_mock: Mock):
    image_cli_mock = Mock()
    image_mock.return_value = image_cli_mock

    test_image_name = "test_dummy_image"

    docker.create(test_image_name, pull="missing")

    image_cli_mock._pull_if_necessary.assert_called_once_with(test_image_name)
    image_cli_mock.pull.assert_not_called()
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd + ["create", test_image_name]
    )


@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container")
@patch("python_on_whales.components.image.cli_wrapper.ImageCLI")
def test_create_always_pull(image_mock: Mock, _: Mock, run_mock: Mock):
    image_cli_mock = Mock()
    image_mock.return_value = image_cli_mock

    test_image_name = "test_dummy_image"

    docker.create(test_image_name, pull="always")

    image_cli_mock._pull_if_necessary.assert_not_called()
    image_cli_mock.pull.assert_called_once_with(test_image_name)
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd + ["create", test_image_name]
    )


@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container")
@patch("python_on_whales.components.image.cli_wrapper.ImageCLI")
def test_create_never_pull(image_mock: Mock, _: Mock, run_mock: Mock):
    image_cli_mock = Mock()
    image_mock.return_value = image_cli_mock

    test_image_name = "test_dummy_image"

    docker.create(test_image_name, pull="never")

    image_cli_mock._pull_if_necessary.assert_not_called()
    image_cli_mock.pull.assert_not_called()
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd + ["create", "--pull", "never", test_image_name]
    )


@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container")
@patch("python_on_whales.components.image.cli_wrapper.ImageCLI")
def test_run_default_pull(image_mock: Mock, _: Mock, run_mock: Mock):
    image_cli_mock = Mock()
    image_mock.return_value = image_cli_mock

    test_image_name = "test_dummy_image"

    docker.run(test_image_name)

    image_cli_mock._pull_if_necessary.assert_called_once_with(test_image_name)
    image_cli_mock.pull.assert_not_called()
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd + ["container", "run", test_image_name],
        tty=False,
        capture_stderr=False,
    )


@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container")
@patch("python_on_whales.components.image.cli_wrapper.ImageCLI")
def test_run_missing_pull(image_mock: Mock, _: Mock, run_mock: Mock):
    image_cli_mock = Mock()
    image_mock.return_value = image_cli_mock

    test_image_name = "test_dummy_image"

    docker.run(test_image_name, pull="missing")

    image_cli_mock._pull_if_necessary.assert_called_once_with(test_image_name)
    image_cli_mock.pull.assert_not_called()
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd + ["container", "run", test_image_name],
        tty=False,
        capture_stderr=False,
    )


@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container")
@patch("python_on_whales.components.image.cli_wrapper.ImageCLI")
def test_run_always_pull(image_mock: Mock, _: Mock, run_mock: Mock):
    image_cli_mock = Mock()
    image_mock.return_value = image_cli_mock

    test_image_name = "test_dummy_image"

    docker.run(test_image_name, pull="always")

    image_cli_mock._pull_if_necessary.assert_not_called()
    image_cli_mock.pull.assert_called_once_with(test_image_name)
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd + ["container", "run", test_image_name],
        tty=False,
        capture_stderr=False,
    )


@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container")
@patch("python_on_whales.components.image.cli_wrapper.ImageCLI")
def test_run_never_pull(image_mock: Mock, _: Mock, run_mock: Mock):
    image_cli_mock = Mock()
    image_mock.return_value = image_cli_mock

    test_image_name = "test_dummy_image"

    docker.run(test_image_name, pull="never")

    image_cli_mock._pull_if_necessary.assert_not_called()
    image_cli_mock.pull.assert_not_called()
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd
        + ["container", "run", "--pull", "never", test_image_name],
        tty=False,
        capture_stderr=False,
    )


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_create_never_pull_error(ctr_client: DockerClient):
    test_image = "alpine:latest"

    if ctr_client.image.exists(test_image):
        ctr_client.image.remove(test_image, force=True)

    with pytest.raises(DockerException):
        ctr_client.container.create(test_image, pull="never")


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_run_never_pull_error(ctr_client: DockerClient):
    test_image = "alpine:latest"

    if ctr_client.image.exists(test_image):
        ctr_client.image.remove(test_image, force=True)

    with pytest.raises(DockerException):
        ctr_client.container.run(test_image, pull="never")


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_create_missing_pull_nonexistent(ctr_client: DockerClient):
    base_image_name = "alpine:latest"

    if ctr_client.image.exists(base_image_name):
        ctr_client.image.remove(base_image_name, force=True)
    assert not ctr_client.image.exists(base_image_name)
    ctr_client.container.create(base_image_name, pull="missing")
    assert ctr_client.image.exists(base_image_name)


def test_create_missing_pull_existent(
    docker_client: DockerClient, tmp_path: Path, docker_registry: str
):
    base_image_name = "alpine:latest"
    test_image_name = f"{docker_registry}/{base_image_name}"

    base_image = docker_client.image.pull(base_image_name)
    base_image.tag(test_image_name)
    docker_client.push(test_image_name)
    remote_id = base_image.id

    (tmp_path / "dodo.txt").write_text("Hello world!")
    updated_image = base_image.copy_to(
        tmp_path / "dodo.txt", "/dada.txt", new_tag=test_image_name
    )
    local_id = updated_image.id

    assert remote_id != local_id
    docker_client.container.create(test_image_name, pull="missing")
    assert docker_client.image.inspect(test_image_name).id == local_id


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_run_missing_pull_nonexistent(ctr_client: DockerClient):
    base_image_name = "alpine:latest"

    if ctr_client.image.exists(base_image_name):
        ctr_client.image.remove(base_image_name, force=True)
    assert not ctr_client.image.exists(base_image_name)
    ctr_client.container.run(base_image_name, pull="missing")
    assert ctr_client.image.exists(base_image_name)


def test_run_missing_pull_existent(
    docker_client: DockerClient, tmp_path: Path, docker_registry: str
):
    base_image_name = "alpine:latest"
    test_image_name = f"{docker_registry}/{base_image_name}"

    base_image = docker_client.image.pull(base_image_name)
    base_image.tag(test_image_name)
    docker_client.push(test_image_name)
    remote_id = base_image.id

    (tmp_path / "dodo.txt").write_text("Hello world!")
    updated_image = base_image.copy_to(
        tmp_path / "dodo.txt", "/dada.txt", new_tag=test_image_name
    )
    local_id = updated_image.id

    assert remote_id != local_id
    docker_client.container.run(test_image_name, pull="missing")
    assert docker_client.image.inspect(test_image_name).id == local_id


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_create_always_pull_nonexistent(ctr_client: DockerClient):
    base_image_name = "alpine:latest"

    if ctr_client.image.exists(base_image_name):
        ctr_client.image.remove(base_image_name, force=True)
    assert not ctr_client.image.exists(base_image_name)
    ctr_client.container.create(base_image_name, pull="always")
    assert ctr_client.image.exists(base_image_name)


def test_create_always_pull_existent(
    docker_client: DockerClient, tmp_path: Path, docker_registry: str
):
    base_image_name = "alpine:latest"
    test_image_name = f"{docker_registry}/{base_image_name}"

    base_image = docker_client.image.pull(base_image_name)
    base_image.tag(test_image_name)
    docker_client.push(test_image_name)
    remote_id = base_image.id

    (tmp_path / "dodo.txt").write_text("Hello world!")
    updated_image = base_image.copy_to(
        tmp_path / "dodo.txt", "/dada.txt", new_tag=test_image_name
    )
    local_id = updated_image.id

    assert remote_id != local_id
    docker_client.container.create(test_image_name, pull="always")
    assert docker_client.image.inspect(test_image_name).id == remote_id


@pytest.mark.parametrize("ctr_client", ["docker", "podman"], indirect=True)
def test_run_always_pull_nonexistent(ctr_client: DockerClient):
    base_image_name = "alpine:latest"

    if ctr_client.image.exists(base_image_name):
        ctr_client.image.remove(base_image_name, force=True)
    assert not ctr_client.image.exists(base_image_name)
    ctr_client.container.run(base_image_name, pull="always")
    assert ctr_client.image.exists(base_image_name)


def test_run_always_pull_existent(
    docker_client: DockerClient, tmp_path: Path, docker_registry: str
):
    base_image_name = "alpine:latest"
    test_image_name = f"{docker_registry}/{base_image_name}"

    base_image = docker_client.image.pull(base_image_name)
    base_image.tag(test_image_name)
    docker_client.push(test_image_name)
    remote_id = base_image.id

    (tmp_path / "dodo.txt").write_text("Hello world!")
    updated_image = base_image.copy_to(
        tmp_path / "dodo.txt", "/dada.txt", new_tag=test_image_name
    )
    local_id = updated_image.id

    assert remote_id != local_id
    docker_client.container.run(test_image_name, pull="always")
    assert docker_client.image.inspect(test_image_name).id == remote_id
