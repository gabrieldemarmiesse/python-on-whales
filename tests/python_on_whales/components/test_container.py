import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from python_on_whales import DockerException, Image, docker
from python_on_whales.components.container import ContainerInspectResult, ContainerState
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
        return docker.build(tmpdir, tags="some_image", return_image=True)


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


# real inspect result
json_container_inspect_1 = """
    {
        "Id": "66b863ddef66ba46671e1350fa6856519b561ff51d7869ccb7caddf22e493065",
        "Created": "2020-09-12T10:54:11.1477412Z",
        "Path": "bash",
        "Args": [
            "-c",
            "service ssh start && sleep infinity"
        ],
        "State": {
            "Status": "running",
            "Running": true,
            "Paused": false,
            "Restarting": false,
            "OOMKilled": false,
            "Dead": false,
            "Pid": 504,
            "ExitCode": 0,
            "Error": "",
            "StartedAt": "2020-10-24T18:23:52.3744635Z",
            "FinishedAt": "2020-10-24T20:23:45.8631404+02:00"
        },
        "Image": "sha256:dd414b47632e477ad90bb82890834adbe96b62718c0f9d1291fdc9b2dc1b2194",
        "ResolvConfPath": "/var/lib/docker/containers/66b863ddef66ba46671e1350fa6856519b561ff51d7869ccb7caddf22e493065/resolv.conf",
        "HostnamePath": "/var/lib/docker/containers/66b863ddef66ba46671e1350fa6856519b561ff51d7869ccb7caddf22e493065/hostname",
        "HostsPath": "/var/lib/docker/containers/66b863ddef66ba46671e1350fa6856519b561ff51d7869ccb7caddf22e493065/hosts",
        "LogPath": "/var/lib/docker/containers/66b863ddef66ba46671e1350fa6856519b561ff51d7869ccb7caddf22e493065/66b863ddef66ba46671e1350fa6856519b561ff51d7869ccb7caddf22e493065-json.log",
        "Name": "/gabriel_work_env",
        "RestartCount": 0,
        "Driver": "overlay2",
        "Platform": "linux",
        "MountLabel": "",
        "ProcessLabel": "",
        "AppArmorProfile": "",
        "ExecIDs": [
            "c2c710292b7b5f59bff54a5cceb1dfe123ffc8747466424e3bcc2cb336d1621e",
            "f35cc96f1f8478947c5ab515ef523b5eeae0c9681f3cf06dd3388f3858c2399b"
        ],
        "HostConfig": {
            "Binds": [
                "apt_cache1:/var/cache/apt",
                "aws_config:/root/.aws/",
                "/mnt:/mnt",
                "/:/host",
                "history:/root/.zsh_history",
                "conda_cache:/opt/conda/pkgs",
                "general_cache:/root/.cache",
                "/var/run/docker.sock:/var/run/docker.sock",
                "/tmp:/tmp",
                "apt_cache2:/var/lib/apt",
                "github_config:/root/.config/gh",
                "/root/.ssh:/root/.ssh",
                "mc_config:/root/.mc/",
                "/root/.secret_envs:/root/.secret_envs",
                "/projects:/projects"
            ],
            "ContainerIDFile": "",
            "LogConfig": {
                "Type": "json-file",
                "Config": {}
            },
            "NetworkMode": "host",
            "PortBindings": {},
            "RestartPolicy": {
                "Name": "no",
                "MaximumRetryCount": 0
            },
            "AutoRemove": false,
            "VolumeDriver": "",
            "VolumesFrom": null,
            "CapAdd": null,
            "CapDrop": null,
            "Capabilities": null,
            "Dns": [],
            "DnsOptions": [],
            "DnsSearch": [],
            "ExtraHosts": null,
            "GroupAdd": null,
            "IpcMode": "private",
            "Cgroup": "",
            "Links": null,
            "OomScoreAdj": 0,
            "PidMode": "host",
            "Privileged": true,
            "PublishAllPorts": false,
            "ReadonlyRootfs": false,
            "SecurityOpt": [
                "label=disable"
            ],
            "UTSMode": "",
            "UsernsMode": "",
            "ShmSize": 67108864,
            "Runtime": "runc",
            "ConsoleSize": [
                0,
                0
            ],
            "Isolation": "",
            "CpuShares": 0,
            "Memory": 0,
            "NanoCpus": 0,
            "CgroupParent": "",
            "BlkioWeight": 0,
            "BlkioWeightDevice": [],
            "BlkioDeviceReadBps": null,
            "BlkioDeviceWriteBps": null,
            "BlkioDeviceReadIOps": null,
            "BlkioDeviceWriteIOps": null,
            "CpuPeriod": 0,
            "CpuQuota": 0,
            "CpuRealtimePeriod": 0,
            "CpuRealtimeRuntime": 0,
            "CpusetCpus": "",
            "CpusetMems": "",
            "Devices": [],
            "DeviceCgroupRules": null,
            "DeviceRequests": null,
            "KernelMemory": 0,
            "KernelMemoryTCP": 0,
            "MemoryReservation": 0,
            "MemorySwap": 0,
            "MemorySwappiness": null,
            "OomKillDisable": false,
            "PidsLimit": null,
            "Ulimits": null,
            "CpuCount": 0,
            "CpuPercent": 0,
            "IOMaximumIOps": 0,
            "IOMaximumBandwidth": 0,
            "MaskedPaths": null,
            "ReadonlyPaths": null
        },
        "GraphDriver": {
            "Data": {
                "LowerDir": "/var/lib/docker/overlay2/44e46fae2a3c4074be061b31b4c8b0abc4391132f854f951a9810551956744f8-init/diff:/var/lib/docker/overlay2/xzpwvat0ezakt6a1h7ll9nck1/diff:/var/lib/docker/overlay2/zf84eg21kky76z7ddxmvz8vfa/diff:/var/lib/docker/overlay2/cjjvfn36fuxxsiobogm0gg7f3/diff:/var/lib/docker/overlay2/zxl45fc9e25x8k0i40h9lb5vb/diff:/var/lib/docker/overlay2/0bc8sskli8ixzt5fx13ckj4s0/diff:/var/lib/docker/overlay2/d875dtxk5e6r2iss5yhgdf9yj/diff:/var/lib/docker/overlay2/b3b6i2tcezdkh120ilja8bx2p/diff:/var/lib/docker/overlay2/hk3g7h0eyratwyvp9r5ur6vcl/diff:/var/lib/docker/overlay2/e6zooh0na09rvz3serhxmre29/diff:/var/lib/docker/overlay2/swl0zwchftcshfyq83j8v31fv/diff:/var/lib/docker/overlay2/e4gath7xzgu4w5ash6ueq6huv/diff:/var/lib/docker/overlay2/xy6vj7yljkl69jwkjdzxm667t/diff:/var/lib/docker/overlay2/j8zzfal20emv9u3q03g8cbvh1/diff:/var/lib/docker/overlay2/m6fgvbl07haaeopyaxcenjzvh/diff:/var/lib/docker/overlay2/ycmn0737mobpd0fbkpb7i1tcd/diff:/var/lib/docker/overlay2/0bgvfynhcjfaypdu2g1qnt4b0/diff:/var/lib/docker/overlay2/ibpomrl3v5t68u39n8718hahm/diff:/var/lib/docker/overlay2/1li4u8u6rvtbs8i194b20iti4/diff:/var/lib/docker/overlay2/sk76f2hbibz9n6xtumf7l16lw/diff:/var/lib/docker/overlay2/uq1m36ccaz8kt6uwihrwankh4/diff:/var/lib/docker/overlay2/rizc4df8wn0i82zg5e7hdmwae/diff:/var/lib/docker/overlay2/7dzf48i0kaonp7u63zik3hrib/diff:/var/lib/docker/overlay2/n9qo9xmmt57ul37kk6e9kumsm/diff:/var/lib/docker/overlay2/mvl575t1qobpu642650ersycs/diff:/var/lib/docker/overlay2/dm64nvfiwk785jg6djlo6s9pm/diff:/var/lib/docker/overlay2/m8l0y7enobhbyb3ql7e7u098n/diff:/var/lib/docker/overlay2/zcb8umiz5w7yat0zs9yu4ha97/diff:/var/lib/docker/overlay2/l61j4xjliko2cpz7ihkh2w3q2/diff:/var/lib/docker/overlay2/tjvvrixd3qbkpbddxcfcls1of/diff:/var/lib/docker/overlay2/qhiz5xexf5l9jfn7yo5m3tlh9/diff:/var/lib/docker/overlay2/h9kryh9galn1qp6vbme507w37/diff:/var/lib/docker/overlay2/m5sg22ger55g1uq7szktq7irw/diff:/var/lib/docker/overlay2/wr7e6odzjoznfc5osp4k83bw0/diff:/var/lib/docker/overlay2/ne0xeyzv5q217oq03vbu4b2ho/diff:/var/lib/docker/overlay2/77q5ywokfiyt2pwu51cuzs40h/diff:/var/lib/docker/overlay2/nva2alkvyk2cmzbycbxrk4ge3/diff:/var/lib/docker/overlay2/iikwojwr9bx4caabf48htsc2p/diff:/var/lib/docker/overlay2/p3hu2y2dr8cmolo2ivxr2e6yz/diff:/var/lib/docker/overlay2/2c7dfa34d1939bfbe2515984678fec40c1beb1f65c54f44fae7208e585fe404e/diff:/var/lib/docker/overlay2/31e22ca1bad00eb9abc9c9658ddc541d4d8c856a6b6fb847016959d6f5b1fa4a/diff:/var/lib/docker/overlay2/9ab72b83f373e2783c2bb1c9753200c476a38560fd19e638fc51c8b877faf6a8/diff:/var/lib/docker/overlay2/adcc31869edc66e8a09772963b687b7c2d52ac140392da99230875cbcaaad8f7/diff",
                "MergedDir": "/var/lib/docker/overlay2/44e46fae2a3c4074be061b31b4c8b0abc4391132f854f951a9810551956744f8/merged",
                "UpperDir": "/var/lib/docker/overlay2/44e46fae2a3c4074be061b31b4c8b0abc4391132f854f951a9810551956744f8/diff",
                "WorkDir": "/var/lib/docker/overlay2/44e46fae2a3c4074be061b31b4c8b0abc4391132f854f951a9810551956744f8/work"
            },
            "Name": "overlay2"
        },
        "Mounts": [
            {
                "Type": "bind",
                "Source": "/mnt",
                "Destination": "/mnt",
                "Mode": "",
                "RW": true,
                "Propagation": "rprivate"
            },
            {
                "Type": "bind",
                "Source": "/root/.secret_envs",
                "Destination": "/root/.secret_envs",
                "Mode": "",
                "RW": true,
                "Propagation": "rprivate"
            },
            {
                "Type": "volume",
                "Name": "apt_cache2",
                "Source": "/var/lib/docker/volumes/apt_cache2/_data",
                "Destination": "/var/lib/apt",
                "Driver": "local",
                "Mode": "z",
                "RW": true,
                "Propagation": ""
            },
            {
                "Type": "bind",
                "Source": "/root/.ssh",
                "Destination": "/root/.ssh",
                "Mode": "",
                "RW": true,
                "Propagation": "rprivate"
            },
            {
                "Type": "volume",
                "Name": "apt_cache1",
                "Source": "/var/lib/docker/volumes/apt_cache1/_data",
                "Destination": "/var/cache/apt",
                "Driver": "local",
                "Mode": "z",
                "RW": true,
                "Propagation": ""
            },
            {
                "Type": "bind",
                "Source": "/",
                "Destination": "/host",
                "Mode": "",
                "RW": true,
                "Propagation": "rslave"
            },
            {
                "Type": "bind",
                "Source": "/projects",
                "Destination": "/projects",
                "Mode": "",
                "RW": true,
                "Propagation": "rprivate"
            },
            {
                "Type": "volume",
                "Name": "github_config",
                "Source": "/var/lib/docker/volumes/github_config/_data",
                "Destination": "/root/.config/gh",
                "Driver": "local",
                "Mode": "z",
                "RW": true,
                "Propagation": ""
            },
            {
                "Type": "volume",
                "Name": "history",
                "Source": "/var/lib/docker/volumes/history/_data",
                "Destination": "/root/.zsh_history",
                "Driver": "local",
                "Mode": "z",
                "RW": true,
                "Propagation": ""
            },
            {
                "Type": "bind",
                "Source": "/tmp",
                "Destination": "/tmp",
                "Mode": "",
                "RW": true,
                "Propagation": "rprivate"
            },
            {
                "Type": "bind",
                "Source": "/var/run/docker.sock",
                "Destination": "/var/run/docker.sock",
                "Mode": "",
                "RW": true,
                "Propagation": "rprivate"
            },
            {
                "Type": "volume",
                "Name": "conda_cache",
                "Source": "/var/lib/docker/volumes/conda_cache/_data",
                "Destination": "/opt/conda/pkgs",
                "Driver": "local",
                "Mode": "z",
                "RW": true,
                "Propagation": ""
            },
            {
                "Type": "volume",
                "Name": "aws_config",
                "Source": "/var/lib/docker/volumes/aws_config/_data",
                "Destination": "/root/.aws",
                "Driver": "local",
                "Mode": "z",
                "RW": true,
                "Propagation": ""
            },
            {
                "Type": "volume",
                "Name": "general_cache",
                "Source": "/var/lib/docker/volumes/general_cache/_data",
                "Destination": "/root/.cache",
                "Driver": "local",
                "Mode": "z",
                "RW": true,
                "Propagation": ""
            },
            {
                "Type": "volume",
                "Name": "mc_config",
                "Source": "/var/lib/docker/volumes/mc_config/_data",
                "Destination": "/root/.mc",
                "Driver": "local",
                "Mode": "z",
                "RW": true,
                "Propagation": ""
            }
        ],
        "Config": {
            "Hostname": "DESKTOP-CGESNGL",
            "Domainname": "",
            "User": "",
            "AttachStdin": false,
            "AttachStdout": false,
            "AttachStderr": false,
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": [
                "PATH=/opt/conda/bin:/root/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "DEBIAN_FRONTEND=noninteractive"
            ],
            "Cmd": [
                "bash",
                "-c",
                "service ssh start && sleep infinity"
            ],
            "Image": "gabrieldemarmiesse/work_env:local_build",
            "Volumes": null,
            "WorkingDir": "",
            "Entrypoint": null,
            "OnBuild": null,
            "Labels": {}
        },
        "NetworkSettings": {
            "Bridge": "",
            "SandboxID": "2c8fd4fc8637a3482a03cffc0f5c23ed4e2563966610f3f1349986e0ee7fc2ea",
            "HairpinMode": false,
            "LinkLocalIPv6Address": "",
            "LinkLocalIPv6PrefixLen": 0,
            "Ports": {},
            "SandboxKey": "/var/run/docker/netns/default",
            "SecondaryIPAddresses": null,
            "SecondaryIPv6Addresses": null,
            "EndpointID": "",
            "Gateway": "",
            "GlobalIPv6Address": "",
            "GlobalIPv6PrefixLen": 0,
            "IPAddress": "",
            "IPPrefixLen": 0,
            "IPv6Gateway": "",
            "MacAddress": "",
            "Networks": {
                "host": {
                    "IPAMConfig": null,
                    "Links": null,
                    "Aliases": null,
                    "NetworkID": "d653dfe9145818498bdb62ca8f405c7ae8eb385e5d85ec0ee5d59e509173003e",
                    "EndpointID": "34887d0b59a366e7d7dceff7849d76085ffd43fbc705cdc24f5583caa42043a5",
                    "Gateway": "",
                    "IPAddress": "",
                    "IPPrefixLen": 0,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "",
                    "DriverOpts": null
                }
            }
        }
    }
"""


def test_container_inspect_result_parsing():
    # a good test would be to parse it, then save it to json
    # and check that it's the same.
    after_parsing = ContainerInspectResult.parse_raw(json_container_inspect_1)
    assert after_parsing.restart_count == 0


sleep_infinity_inspect = """
    {
        "Id": "2a082be0cdfbd7f8d181170d8d0bf2137a4340ba486a54c30ddd5d036992a674",
        "Created": "2020-10-24T19:06:27.4886343Z",
        "Path": "sleep",
        "Args": [
            "infinity"
        ],
        "State": {
            "Status": "running",
            "Running": true,
            "Paused": false,
            "Restarting": false,
            "OOMKilled": false,
            "Dead": false,
            "Pid": 8811,
            "ExitCode": 0,
            "Error": "",
            "StartedAt": "2020-10-24T19:06:27.7692114Z",
            "FinishedAt": "0001-01-01T00:00:00Z"
        },
        "Image": "sha256:9140108b62dc87d9b278bb0d4fd6a3e44c2959646eb966b86531306faa81b09b",
        "ResolvConfPath": "/var/lib/docker/containers/2a082be0cdfbd7f8d181170d8d0bf2137a4340ba486a54c30ddd5d036992a674/resolv.conf",
        "HostnamePath": "/var/lib/docker/containers/2a082be0cdfbd7f8d181170d8d0bf2137a4340ba486a54c30ddd5d036992a674/hostname",
        "HostsPath": "/var/lib/docker/containers/2a082be0cdfbd7f8d181170d8d0bf2137a4340ba486a54c30ddd5d036992a674/hosts",
        "LogPath": "/var/lib/docker/containers/2a082be0cdfbd7f8d181170d8d0bf2137a4340ba486a54c30ddd5d036992a674/2a082be0cdfbd7f8d181170d8d0bf2137a4340ba486a54c30ddd5d036992a674-json.log",
        "Name": "/interesting_perlman",
        "RestartCount": 0,
        "Driver": "overlay2",
        "Platform": "linux",
        "MountLabel": "",
        "ProcessLabel": "",
        "AppArmorProfile": "",
        "ExecIDs": null,
        "HostConfig": {
            "Binds": null,
            "ContainerIDFile": "",
            "LogConfig": {
                "Type": "json-file",
                "Config": {}
            },
            "NetworkMode": "default",
            "PortBindings": {},
            "RestartPolicy": {
                "Name": "no",
                "MaximumRetryCount": 0
            },
            "AutoRemove": false,
            "VolumeDriver": "",
            "VolumesFrom": null,
            "CapAdd": null,
            "CapDrop": null,
            "Capabilities": null,
            "Dns": [],
            "DnsOptions": [],
            "DnsSearch": [],
            "ExtraHosts": null,
            "GroupAdd": null,
            "IpcMode": "private",
            "Cgroup": "",
            "Links": null,
            "OomScoreAdj": 0,
            "PidMode": "",
            "Privileged": false,
            "PublishAllPorts": false,
            "ReadonlyRootfs": false,
            "SecurityOpt": null,
            "UTSMode": "",
            "UsernsMode": "",
            "ShmSize": 67108864,
            "Runtime": "runc",
            "ConsoleSize": [
                0,
                0
            ],
            "Isolation": "",
            "CpuShares": 0,
            "Memory": 0,
            "NanoCpus": 0,
            "CgroupParent": "",
            "BlkioWeight": 0,
            "BlkioWeightDevice": [],
            "BlkioDeviceReadBps": null,
            "BlkioDeviceWriteBps": null,
            "BlkioDeviceReadIOps": null,
            "BlkioDeviceWriteIOps": null,
            "CpuPeriod": 0,
            "CpuQuota": 0,
            "CpuRealtimePeriod": 0,
            "CpuRealtimeRuntime": 0,
            "CpusetCpus": "",
            "CpusetMems": "",
            "Devices": [],
            "DeviceCgroupRules": null,
            "DeviceRequests": null,
            "KernelMemory": 0,
            "KernelMemoryTCP": 0,
            "MemoryReservation": 0,
            "MemorySwap": 0,
            "MemorySwappiness": null,
            "OomKillDisable": false,
            "PidsLimit": null,
            "Ulimits": null,
            "CpuCount": 0,
            "CpuPercent": 0,
            "IOMaximumIOps": 0,
            "IOMaximumBandwidth": 0,
            "MaskedPaths": [
                "/proc/asound",
                "/proc/acpi",
                "/proc/kcore",
                "/proc/keys",
                "/proc/latency_stats",
                "/proc/timer_list",
                "/proc/timer_stats",
                "/proc/sched_debug",
                "/proc/scsi",
                "/sys/firmware"
            ],
            "ReadonlyPaths": [
                "/proc/bus",
                "/proc/fs",
                "/proc/irq",
                "/proc/sys",
                "/proc/sysrq-trigger"
            ]
        },
        "GraphDriver": {
            "Data": {
                "LowerDir": "/var/lib/docker/overlay2/d4353d11863e710c2588e34755441d3048c0ee2abef848afd01d22cfe019fab8-init/diff:/var/lib/docker/overlay2/a2ea58265f386135f2c639d2e2723fd8335451800306209e4f0c4214e577183b/diff:/var/lib/docker/overlay2/a7d0a2c86da75e7a8a11784af8e3e274172cee8787b2af0b0ce5b3fa4ef51e2a/diff:/var/lib/docker/overlay2/84025c095722b771cb9231e1e7defe55e8a543dc87619f1437d6a6d5be489392/diff",
                "MergedDir": "/var/lib/docker/overlay2/d4353d11863e710c2588e34755441d3048c0ee2abef848afd01d22cfe019fab8/merged",
                "UpperDir": "/var/lib/docker/overlay2/d4353d11863e710c2588e34755441d3048c0ee2abef848afd01d22cfe019fab8/diff",
                "WorkDir": "/var/lib/docker/overlay2/d4353d11863e710c2588e34755441d3048c0ee2abef848afd01d22cfe019fab8/work"
            },
            "Name": "overlay2"
        },
        "Mounts": [],
        "Config": {
            "Hostname": "2a082be0cdfb",
            "Domainname": "",
            "User": "",
            "AttachStdin": false,
            "AttachStdout": false,
            "AttachStderr": false,
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ],
            "Cmd": [
                "sleep",
                "infinity"
            ],
            "Image": "ubuntu",
            "Volumes": null,
            "WorkingDir": "",
            "Entrypoint": null,
            "OnBuild": null,
            "Labels": {}
        },
        "NetworkSettings": {
            "Bridge": "",
            "SandboxID": "c2eb608610c6dce2f66145c0fda027b73bdd04c99786b58544862e396f6f2bd3",
            "HairpinMode": false,
            "LinkLocalIPv6Address": "",
            "LinkLocalIPv6PrefixLen": 0,
            "Ports": {},
            "SandboxKey": "/var/run/docker/netns/c2eb608610c6",
            "SecondaryIPAddresses": null,
            "SecondaryIPv6Addresses": null,
            "EndpointID": "c906f72221637f06e895f708717344180a813a2729a74b9593f3ae7b5cd52790",
            "Gateway": "172.17.0.1",
            "GlobalIPv6Address": "",
            "GlobalIPv6PrefixLen": 0,
            "IPAddress": "172.17.0.2",
            "IPPrefixLen": 16,
            "IPv6Gateway": "",
            "MacAddress": "02:42:ac:11:00:02",
            "Networks": {
                "bridge": {
                    "IPAMConfig": null,
                    "Links": null,
                    "Aliases": null,
                    "NetworkID": "e290f3539fbb8d960ff77af0b84d91a640bf50ec0bd56edd5fd22adcb1befbb4",
                    "EndpointID": "c906f72221637f06e895f708717344180a813a2729a74b9593f3ae7b5cd52790",
                    "Gateway": "172.17.0.1",
                    "IPAddress": "172.17.0.2",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "02:42:ac:11:00:02",
                    "DriverOpts": null
                }
            }
        }
    }
"""


def test_container_inspect_result_parsing_sleep_infinity():
    # a good test would be to parse it, then save it to json
    # and check that it's the same.
    after_parsing = ContainerInspectResult.parse_raw(sleep_infinity_inspect)
    assert after_parsing.restart_count == 0
