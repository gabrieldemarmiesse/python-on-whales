import json
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import python_on_whales
from python_on_whales import DockerException, Image, docker
from python_on_whales.components.container.cli_wrapper import ContainerStats
from python_on_whales.components.container.models import (
    ContainerInspectResult,
    ContainerState,
)
from python_on_whales.test_utils import get_all_jsons, random_name


@pytest.mark.parametrize("json_file", get_all_jsons("containers"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    ContainerInspectResult.parse_raw(json_as_txt)
    # we could do more checks here if needed


def test_simple_command():
    output = docker.run("hello-world", remove=True)
    assert "Hello from Docker!" in output


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
    container = docker.run("busybox:1", ["echo", "dodo"], detach=True)
    time.sleep(0.3)
    output = docker.container.logs(container)
    assert output == "dodo"


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
    a = ContainerState.parse_raw(json_state)

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
    docker.container.stop([])


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
