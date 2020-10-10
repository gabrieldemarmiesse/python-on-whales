import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from python_on_whales import DockerException, Image, docker
from python_on_whales.components.container import ContainerState
from python_on_whales.test_utils import random_name


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
        return docker.build(tmpdir, tags="some_image")


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
    assert a.running == True
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
    assert my_container.state.running == False
    my_container.remove()


def test_context_manager():
    container_name = random_name()
    with pytest.raises(ArithmeticError):
        with docker.run(
            "busybox:1", ["sleep", "infinity"], detach=True, name=container_name
        ) as c:
            raise ArithmeticError

    assert container_name not in [x.name for x in docker.container.list(all=True)]


def test_context_manager_with_create():
    container_name = random_name()
    with pytest.raises(ArithmeticError):
        with docker.container.create(
            "busybox:1", ["sleep", "infinity"], name=container_name
        ) as c:
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
