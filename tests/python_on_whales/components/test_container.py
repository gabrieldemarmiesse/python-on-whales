import json
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
from python_on_whales import Image, docker
from python_on_whales.components.container.cli_wrapper import ContainerStats
from python_on_whales.components.container.models import (
    ContainerInspectResult,
    ContainerState,
)
from python_on_whales.exceptions import DockerException, NoSuchContainer
from python_on_whales.test_utils import get_all_jsons, random_name


@pytest.mark.parametrize("json_file", get_all_jsons("containers"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ContainerInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


def test_simple_command():
    output = docker.run("hello-world", remove=True)
    assert "Hello from Docker!" in output


def test_simple_mistake_on_run():
    with pytest.raises(TypeError) as err:
        docker.run("ubuntu", "ls")
    assert "docker.run('ubuntu', ['ls'], ...)" in str(err)
    docker.run("ubuntu", ["ls"], remove=True)


def test_simple_command_create_start():
    output = docker.container.create("hello-world", remove=True).start(attach=True)
    assert "Hello from Docker!" in output


def test_simple_stream():
    output = docker.run("hello-world", remove=True, stream=True)

    assert ("stdout", b"Hello from Docker!\n") in list(output)


def test_simple_stream_create_start():
    container = docker.container.create("hello-world", remove=True)
    output = container.start(attach=True, stream=True)
    assert ("stdout", b"Hello from Docker!\n") in list(output)


def test_same_output_run_create_start():
    python_code = """
import sys
sys.stdout.write("everything is fine\\n\\nhello world")
sys.stderr.write("Something is wrong!")
    """
    image = build_image_running(python_code)
    output_run = docker.run(image, remove=True)
    output_create = docker.container.create(image, remove=True).start(attach=True)
    assert output_run == output_create


def test_same_stream_run_create_start():
    python_code = """
import sys
sys.stdout.write("everything is fine\\n\\nhello world")
sys.stderr.write("Something is wrong!")
    """
    image = build_image_running(python_code)
    output_run = set(docker.run(image, remove=True, stream=True))
    container = docker.container.create(image, remove=True)
    output_create = set(container.start(attach=True, stream=True))
    assert output_run == output_create


def test_exact_output():
    try:
        docker.image.remove("busybox")
    except DockerException:
        pass
    assert docker.run("busybox", ["echo", "dodo"], remove=True) == "dodo"


def build_image_running(python_code) -> Image:
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
        return docker.build(tmpdir, tags="some_image", load=True)


def test_fails_correctly():
    python_code = """
import sys
sys.stdout.write("everything is fine")
sys.stderr.write("Something is wrong!")
sys.exit(1)
"""
    image = build_image_running(python_code)
    with image:
        with pytest.raises(DockerException) as err:
            for _ in docker.run(image, stream=True, remove=True):
                pass
        assert "Something is wrong!" in str(err.value)


def test_container_repr():
    with docker.run(
        "ubuntu",
        ["sleep", "infinity"],
        remove=True,
        detach=True,
        stop_timeout=1,
    ) as container:
        assert container.id[:12] in repr(docker.container.list())


def test_container_run_with_random_port():
    with docker.run(
        "ubuntu",
        ["sleep", "infinity"],
        publish=[(90,)],
        remove=True,
        detach=True,
        stop_timeout=1,
    ) as container:
        assert container.network_settings.ports["90/tcp"][0]["HostPort"] is not None
        assert container.id[:12] in repr(docker.container.list())


def test_container_create_with_random_ports():
    with docker.container.create(
        "ubuntu", ["sleep", "infinity"], publish=[(90,)], stop_timeout=1
    ) as container:
        container.start()
        assert container.network_settings.ports["90/tcp"][0]["HostPort"] is not None


def test_container_create_with_cgroupns():
    with docker.container.run(
        "ubuntu", ["sleep", "infinity"], cgroupns="host", detach=True, stop_timeout=1
    ) as container:
        assert container.host_config.cgroupns_mode == "host"


@pytest.mark.parametrize("systemd_mode", [True, False, "always"])
@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container", Mock())
def test_container_create_with_systemd_mode(
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


def test_fails_correctly_create_start():
    python_code = """
import sys
sys.stdout.write("everything is fine")
sys.stderr.write("Something is wrong!")
sys.exit(1)
"""
    image = build_image_running(python_code)
    with image:
        container = docker.container.create(image, remove=True)
        with pytest.raises(DockerException) as err:
            for _ in container.start(attach=True, stream=True):
                pass
        assert "Something is wrong!" in str(err.value)


def test_remove():
    output = docker.run("hello-world", remove=True)
    assert "Hello from Docker!" in output


def test_cpus():
    output = docker.run("hello-world", cpus=1.5, remove=True)
    assert "Hello from Docker!" in output


def test_run_volumes():
    volume_name = random_name()
    docker.run(
        "busybox",
        ["touch", "/some/path/dodo"],
        volumes=[(volume_name, "/some/path")],
        remove=True,
    )
    docker.volume.remove(volume_name)


def test_container_remove():
    container = docker.run("hello-world", detach=True)
    time.sleep(0.3)
    assert container in docker.container.list(all=True)
    docker.container.remove(container)
    assert container not in docker.container.list(all=True)


def test_simple_logs():
    with docker.run("busybox:1", ["echo", "dodo"], detach=True) as c:
        time.sleep(0.3)
        output = docker.container.logs(c)
        assert output == "dodo\n"


def test_simple_logs_stderr():
    with docker.run("busybox:1", ["sh", "-c", ">&2 echo dodo"], detach=True) as c:
        time.sleep(0.3)
        output = docker.container.logs(c)
        assert output == "dodo\n"


def test_simple_logs_do_not_follow():
    with docker.run(
        "busybox:1", ["sh", "-c", "sleep 3 && echo dodo"], detach=True
    ) as c:
        output = docker.container.logs(c, follow=False)
        assert output == ""


def test_simple_logs_follow():
    with docker.run(
        "busybox:1", ["sh", "-c", "sleep 3 && echo dodo"], detach=True
    ) as c:
        output = docker.container.logs(c, follow=True)
        assert output == "dodo\n"


def test_simple_logs_stream():
    with docker.run("busybox:1", ["echo", "dodo"], detach=True) as c:
        time.sleep(0.3)
        output = list(docker.container.logs(c, stream=True))
        assert output == [("stdout", b"dodo\n")]


def test_simple_logs_stream_stderr():
    with docker.run("busybox:1", ["sh", "-c", ">&2 echo dodo"], detach=True) as c:
        time.sleep(0.3)
        output = list(docker.container.logs(c, stream=True))
        assert output == [("stderr", b"dodo\n")]


def test_simple_logs_stream_stdout_and_stderr():
    with docker.run(
        "busybox:1", ["sh", "-c", ">&2 echo dodo && echo dudu"], detach=True
    ) as c:
        time.sleep(0.3)
        output = list(docker.container.logs(c, stream=True))

        # the order of stderr and stdout is not guaranteed.
        assert set(output) == {("stderr", b"dodo\n"), ("stdout", b"dudu\n")}


def test_simple_logs_stream_wait():
    with docker.run(
        "busybox:1", ["sh", "-c", "sleep 3 && echo dodo"], detach=True
    ) as c:
        time.sleep(0.3)
        output = list(docker.container.logs(c, follow=True, stream=True))
        assert output == [("stdout", b"dodo\n")]


def test_rename():
    name = random_name()
    new_name = random_name()
    assert name != new_name
    container = docker.container.run("hello-world", name=name, detach=True)
    docker.container.rename(container, new_name)
    container.reload()

    assert container.name == new_name
    docker.container.remove(container)


def test_name():
    name = random_name()
    container = docker.container.run("hello-world", name=name, detach=True)
    assert container.name == name
    docker.container.remove(container)


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


def test_container_state():
    a = ContainerState(**json.loads(json_state))

    assert a.status == "running"
    assert a.running
    assert a.exit_code == 0
    assert a.finished_at == datetime(
        2020, 9, 2, 22, 14, 50, 462597, tzinfo=timezone(timedelta(hours=2))
    )


def test_restart():
    cmd = ["sleep", "infinity"]
    containers = [docker.run("busybox:1", cmd, detach=True) for _ in range(3)]
    docker.kill(containers)

    docker.restart(containers)
    for container in containers:
        assert container.state.running


def test_execute():
    my_container = docker.run(
        "busybox:1", ["sleep", "infinity"], detach=True, remove=True
    )
    exec_result = docker.execute(my_container, ["echo", "dodo"])
    assert exec_result == "dodo"
    docker.kill(my_container)


def test_execute_simple_mistake():
    with docker.run(
        "busybox:1", ["sleep", "infinity"], detach=True, remove=True
    ) as my_container:
        with pytest.raises(TypeError) as err:
            docker.execute(my_container, "echo dodo")
        assert f"docker.execute('{my_container.name}', ['echo', 'dodo'], ...)" in str(
            err
        )


def test_execute_stream():
    my_container = docker.run(
        "busybox:1", ["sleep", "infinity"], detach=True, remove=True
    )
    exec_result = list(
        docker.execute(my_container, ["sh", "-c", ">&2 echo dodo"], stream=True)
    )
    assert exec_result == [("stderr", b"dodo\n")]
    docker.kill(my_container)


def test_diff():
    my_container = docker.run(
        "busybox:1", ["sleep", "infinity"], detach=True, remove=True
    )

    docker.execute(my_container, ["mkdir", "/some_path"])
    docker.execute(my_container, ["touch", "/some_file"])
    docker.execute(my_container, ["rm", "-rf", "/tmp"])

    diff = docker.diff(my_container)
    assert diff == {"/some_path": "A", "/some_file": "A", "/tmp": "D"}
    docker.kill(my_container)


def test_methods():
    my_container = docker.run("busybox:1", ["sleep", "infinity"], detach=True)
    my_container.kill()
    assert not my_container.state.running
    my_container.remove()


def test_kill_signal():
    my_container = docker.run(
        "busybox:1", ["sleep", "infinity"], init=True, detach=True
    )
    my_container.kill(signal=signal.SIGINT)
    assert not my_container.state.running
    assert my_container.state.exit_code == 130
    my_container.remove()


def test_context_manager():
    container_name = random_name()
    with pytest.raises(ArithmeticError):
        with docker.run(
            "busybox:1", ["sleep", "infinity"], detach=True, name=container_name
        ):
            raise ArithmeticError

    assert container_name not in [x.name for x in docker.container.list(all=True)]


def test_context_manager_with_create():
    container_name = random_name()
    with pytest.raises(ArithmeticError):
        with docker.container.create(
            "busybox:1", ["sleep", "infinity"], name=container_name
        ) as c:
            assert isinstance(c, python_on_whales.Container)
            raise ArithmeticError

    assert container_name not in [x.name for x in docker.container.list(all=True)]


def test_filters():
    random_label_value = random_name()

    containers_with_labels = []

    for _ in range(3):
        containers_with_labels.append(
            docker.run(
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
            docker.run(
                "busybox",
                ["sleep", "infinity"],
                remove=True,
                detach=True,
                labels=dict(dodo="something"),
            )
        )

    expected_containers_with_labels = docker.container.list(
        filters=dict(label=f"dodo={random_label_value}")
    )

    assert set(expected_containers_with_labels) == set(containers_with_labels)

    for container in containers_with_labels + containers_with_wrong_labels:
        container.kill()


def test_wait_single_container():
    cont_1 = docker.run("busybox", ["sh", "-c", "sleep 2 && exit 8"], detach=True)
    with cont_1:
        exit_code = docker.wait(cont_1)

    assert exit_code == 8


def test_wait_single_container_already_finished():
    cont_1 = docker.run("busybox", ["sh", "-c", "exit 8"], detach=True)
    first_exit_code = docker.wait(cont_1)
    second_exit_code = docker.wait(cont_1)

    assert first_exit_code == second_exit_code == 8


def test_wait_multiple_container():
    cont_1 = docker.run("busybox", ["sh", "-c", "sleep 2 && exit 8"], detach=True)
    cont_2 = docker.run("busybox", ["sh", "-c", "sleep 2 && exit 10"], detach=True)

    with cont_1, cont_2:
        exit_codes = docker.wait([cont_1, cont_2])

    assert exit_codes == [8, 10]


def test_wait_multiple_container_random_exit_order():
    cont_1 = docker.run("busybox", ["sh", "-c", "sleep 4 && exit 8"], detach=True)
    cont_2 = docker.run("busybox", ["sh", "-c", "sleep 2 && exit 10"], detach=True)

    with cont_1, cont_2:
        exit_codes = docker.wait([cont_1, cont_2])

    assert exit_codes == [8, 10]


def test_pause_unpause():
    container = docker.run(
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


def test_docker_stats():
    with docker.run(
        "busybox", ["sleep", "infinity"], detach=True, stop_timeout=1
    ) as container:
        for stat in docker.stats():
            if stat.container_id == container.id:
                break
        assert stat.container_name == container.name
        assert stat.cpu_percentage <= 5
        assert stat.memory_used <= 100_000_000


def test_docker_stats_container() -> None:
    with docker.run("busybox", ["sleep", "infinity"], detach=True) as container:
        with docker.run("busybox", ["sleep", "infinity"], detach=True) as _:
            stats = docker.stats(containers=[container.id])
            assert len(stats) == 1
            assert stats[0].container_name == container.name


@patch("python_on_whales.components.container.cli_wrapper.run")
def test_docker_stats_cli_default(run_mock: Mock) -> None:
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
def test_docker_stats_cli_container(run_mock: Mock) -> None:
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


def test_docker_stats_cli_empty_selection() -> None:
    assert docker.container.stats(containers=[]) == []


def test_remove_anonymous_volume_too():
    container = docker.run("postgres:9.6.20-alpine", detach=True)

    volume_id = container.mounts[0].name
    volume = docker.volume.inspect(volume_id)

    with container:
        pass

    assert volume not in docker.volume.list()
    assert container not in docker.ps(all=True)


def test_remove_nothing():
    docker.container.remove([])


def test_stop_nothing():
    docker.container.stop([])


def test_kill_nothing():
    with docker.run("ubuntu", ["sleep", "infinity"], detach=True, remove=True):
        set_of_containers = set(docker.ps())
        docker.container.kill([])
        assert set_of_containers == set(docker.ps())


def test_exec_env():
    with docker.run("ubuntu", ["sleep", "infinity"], detach=True, remove=True) as c:
        result = c.execute(["bash", "-c", "echo $DODO"], envs={"DODO": "dada"})

    assert result == "dada"


def test_exec_env_file(tmp_path):
    env_file = tmp_path / "variables.env"
    env_file.write_text("DODO=dada\n")

    with docker.run("ubuntu", ["sleep", "infinity"], detach=True, remove=True) as c:
        result = c.execute(["bash", "-c", "echo $DODO"], env_files=[env_file])
    assert result == "dada"


def test_export_file(tmp_path):
    dest = tmp_path / "dodo.tar"
    with docker.run("busybox", ["sleep", "infinity"], detach=True, remove=True) as c:
        c.export(dest)

    assert dest.exists()
    assert dest.stat().st_size > 10_000


def test_exec_privilged_flag(mocker):
    fake_completed_process = mocker.MagicMock()
    fake_completed_process.returncode = 0

    patched_run = mocker.patch("subprocess.run")
    patched_run.return_value = fake_completed_process
    docker.execute("my_container", ["some_command"], privileged=True)

    assert patched_run.call_args[0][0][1:] == [
        "exec",
        "--privileged",
        "my_container",
        "some_command",
    ]


def test_exec_change_user():
    with docker.run("ubuntu", ["sleep", "infinity"], detach=True, remove=True) as c:
        c.execute(["useradd", "-ms", "/bin/bash", "newuser"])
        assert c.execute(["whoami"], user="newuser") == "newuser"


def test_exec_change_directory():
    with docker.run("ubuntu", ["sleep", "infinity"], detach=True, remove=True) as c:
        assert c.execute(["pwd"], workdir="/tmp") == "/tmp"
        assert c.execute(["pwd"], workdir="/etc") == "/etc"
        assert c.execute(["pwd"], workdir="/usr/lib") == "/usr/lib"


@pytest.mark.parametrize(
    "docker_function",
    [
        docker.container.attach,
        docker.container.commit,
        docker.container.diff,
        docker.container.inspect,
        docker.container.kill,
        docker.container.logs,
        docker.container.pause,
        docker.container.remove,
        docker.container.restart,
        docker.container.start,
        docker.container.stop,
        docker.container.unpause,
        docker.container.wait,
    ],
)
def test_functions_nosuchcontainer(docker_function):
    with pytest.raises(NoSuchContainer):
        docker_function("DOODODGOIHURHURI")


def test_copy_nosuchcontainer():
    with pytest.raises(NoSuchContainer):
        docker.container.copy(("dodueizbgueirzhgueoz", "/dududada"), "/tmp/dudufeoz")


def test_execute_nosuchcontainer():
    with pytest.raises(NoSuchContainer):
        docker.container.execute("dodueizbgueirzhgueoz", ["echo", "dudu"])


def test_export_nosuchcontainer(tmp_path):
    dest = tmp_path / "dodo.tar"
    with pytest.raises(NoSuchContainer):
        docker.container.export("some_random_container_that_does_not_exists", dest)


def test_rename_nosuchcontainer():
    with pytest.raises(NoSuchContainer):
        docker.container.rename("dodueizbgueirzhgueoz", "new_name")


def test_update_nosuchcontainer():
    with pytest.raises(NoSuchContainer):
        docker.container.update("grueighuri", cpus=1)


def test_prune():
    for container in docker.container.list(filters={"name": "test-container"}):
        docker.container.remove(container, force=True)
    container = docker.container.create("busybox")
    assert container in docker.container.list(all=True)

    # container not pruned because it is not old enough
    docker.container.prune(filters={"until": "100h"})
    assert container in docker.container.list(all=True)

    # container not pruned because it is does not have label "dne"
    docker.container.prune(filters={"label": "dne"})
    assert container in docker.container.list(all=True)

    # container not pruned because it is not old enough and does not have label "dne"
    docker.container.prune(filters={"until": "100h", "label": "dne"})
    assert container in docker.container.list(all=True)

    # container pruned
    docker.container.prune()
    assert container not in docker.container.list(all=True)


def test_run_detached_interactive():
    with docker.run("ubuntu", interactive=True, detach=True, tty=False) as c:
        c.execute(["true"])


@patch("python_on_whales.components.container.cli_wrapper.ContainerCLI.inspect")
@patch("python_on_whales.components.container.cli_wrapper.run")
def test_attach_default(run_mock: Mock, inspect_mock: Mock) -> None:
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
def test_attach_detach_keys_argument(run_mock: Mock, inspect_mock: Mock) -> None:
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
def test_attach_no_stdin_argument(run_mock: Mock, inspect_mock: Mock) -> None:
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
def test_attach_sig_proxy_argument(run_mock: Mock, inspect_mock: Mock) -> None:
    test_container_name = "test_dummy_container"

    docker.attach(test_container_name, sig_proxy=False)

    inspect_mock.assert_called_once_with(test_container_name)
    run_mock.assert_called_once_with(
        docker.client_config.docker_cmd + ["attach", test_container_name], tty=True
    )


@patch("python_on_whales.components.container.cli_wrapper.run")
@patch("python_on_whales.components.container.cli_wrapper.Container")
@patch("python_on_whales.components.image.cli_wrapper.ImageCLI")
def test_container_create_default_pull(
    image_mock: Mock, _: Mock, run_mock: Mock
) -> None:
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
def test_container_create_missing_pull(
    image_mock: Mock, _: Mock, run_mock: Mock
) -> None:
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
def test_container_create_always_pull(
    image_mock: Mock, _: Mock, run_mock: Mock
) -> None:
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
def test_container_create_never_pull(image_mock: Mock, _: Mock, run_mock: Mock) -> None:
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
def test_container_run_default_pull(image_mock: Mock, _: Mock, run_mock: Mock) -> None:
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
def test_container_run_missing_pull(image_mock: Mock, _: Mock, run_mock: Mock) -> None:
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
def test_container_run_always_pull(image_mock: Mock, _: Mock, run_mock: Mock) -> None:
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
def test_container_run_never_pull(image_mock: Mock, _: Mock, run_mock: Mock) -> None:
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


def test_container_call_create_never_pull_error() -> None:
    test_image = "alpine:latest"

    if docker.image.exists(test_image):
        docker.image.remove(test_image, force=True)

    with pytest.raises(DockerException):
        docker.container.create(test_image, pull="never")


def test_container_call_run_never_pull_error() -> None:
    test_image = "alpine:latest"

    if docker.image.exists(test_image):
        docker.image.remove(test_image, force=True)

    with pytest.raises(DockerException):
        docker.container.run(test_image, pull="never")


def test_container_call_create_missing_pull_unexistent() -> None:
    base_image_name = "alpine:latest"

    if docker.image.exists(base_image_name):
        docker.image.remove(base_image_name, force=True)
    assert not docker.image.exists(base_image_name)
    docker.container.create(base_image_name, pull="missing")
    assert docker.image.exists(base_image_name)


def test_container_call_create_missing_pull_existent(tmp_path, docker_registry) -> None:
    base_image_name = "alpine:latest"
    test_image_name = f"{docker_registry}/{base_image_name}"

    base_image = docker.image.pull(base_image_name)
    base_image.tag(test_image_name)
    docker.push(test_image_name)
    remote_id = base_image.id

    (tmp_path / "dodo.txt").write_text("Hello world!")
    updated_image = base_image.copy_to(
        tmp_path / "dodo.txt", "/dada.txt", new_tag=test_image_name
    )
    local_id = updated_image.id

    assert remote_id != local_id
    docker.container.create(test_image_name, pull="missing")
    assert docker.image.inspect(test_image_name).id == local_id


def test_container_call_run_missing_pull_unexistent() -> None:
    base_image_name = "alpine:latest"

    if docker.image.exists(base_image_name):
        docker.image.remove(base_image_name, force=True)
    assert not docker.image.exists(base_image_name)
    docker.container.run(base_image_name, pull="missing")
    assert docker.image.exists(base_image_name)


def test_container_call_run_missing_pull_existent(tmp_path, docker_registry) -> None:
    base_image_name = "alpine:latest"
    test_image_name = f"{docker_registry}/{base_image_name}"

    base_image = docker.image.pull(base_image_name)
    base_image.tag(test_image_name)
    docker.push(test_image_name)
    remote_id = base_image.id

    (tmp_path / "dodo.txt").write_text("Hello world!")
    updated_image = base_image.copy_to(
        tmp_path / "dodo.txt", "/dada.txt", new_tag=test_image_name
    )
    local_id = updated_image.id

    assert remote_id != local_id
    docker.container.run(test_image_name, pull="missing")
    assert docker.image.inspect(test_image_name).id == local_id


def test_container_call_create_always_pull_unexistent() -> None:
    base_image_name = "alpine:latest"

    if docker.image.exists(base_image_name):
        docker.image.remove(base_image_name, force=True)
    assert not docker.image.exists(base_image_name)
    docker.container.create(base_image_name, pull="always")
    assert docker.image.exists(base_image_name)


def test_container_call_create_always_pull_existent(tmp_path, docker_registry) -> None:
    base_image_name = "alpine:latest"
    test_image_name = f"{docker_registry}/{base_image_name}"

    base_image = docker.image.pull(base_image_name)
    base_image.tag(test_image_name)
    docker.push(test_image_name)
    remote_id = base_image.id

    (tmp_path / "dodo.txt").write_text("Hello world!")
    updated_image = base_image.copy_to(
        tmp_path / "dodo.txt", "/dada.txt", new_tag=test_image_name
    )
    local_id = updated_image.id

    assert remote_id != local_id
    docker.container.create(test_image_name, pull="always")
    assert docker.image.inspect(test_image_name).id == remote_id


def test_container_call_run_always_pull_unexistent() -> None:
    base_image_name = "alpine:latest"

    if docker.image.exists(base_image_name):
        docker.image.remove(base_image_name, force=True)
    assert not docker.image.exists(base_image_name)
    docker.container.run(base_image_name, pull="always")
    assert docker.image.exists(base_image_name)


def test_container_call_run_always_pull_existent(tmp_path, docker_registry) -> None:
    base_image_name = "alpine:latest"
    test_image_name = f"{docker_registry}/{base_image_name}"

    base_image = docker.image.pull(base_image_name)
    base_image.tag(test_image_name)
    docker.push(test_image_name)
    remote_id = base_image.id

    (tmp_path / "dodo.txt").write_text("Hello world!")
    updated_image = base_image.copy_to(
        tmp_path / "dodo.txt", "/dada.txt", new_tag=test_image_name
    )
    local_id = updated_image.id

    assert remote_id != local_id
    docker.container.run(test_image_name, pull="always")
    assert docker.image.inspect(test_image_name).id == remote_id
