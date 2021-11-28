import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from queue import Queue
from subprocess import PIPE, Popen
from threading import Thread
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import pydantic

from python_on_whales.exceptions import (
    DockerException,
    NoSuchContainer,
    NoSuchImage,
    NoSuchService,
    NoSuchVolume,
    NotASwarmManager,
)

PROJECT_ROOT = Path(__file__).parents[1]


def title_if_necessary(string: str):
    if string.isupper():
        return string
    else:
        return string.title()


def to_docker_camel(string):
    try:
        special_cases = {
            "exec_ids": "ExecIDs",
            "sandbox_id": "SandboxID",
            "oom_killed": "OOMKilled",
            "rw": "RW",
            "link_local_ipv6_address": "LinkLocalIPv6Address",
            "link_local_ipv6_prefix_lenght": "LinkLocalIPv6PrefixLen",
            "secondary_ipv6_addresses": "SecondaryIPv6Addresses",
            "endpoint_id": "EndpointID",
            "global_ipv6_prefix_lenght": "GlobalIPv6PrefixLen",
            "ip_prefix_lenght": "IPPrefixLen",
            "ipv6_gateway": "IPv6Gateway",
            "network_id": "NetworkID",
            "ip_address": "IPAddress",
            "global_ipv6_address": "GlobalIPv6Address",
            "blkio_device_read_iops": "BlkioDeviceReadIOps",
            "blkio_device_write_iops": "BlkioDeviceWriteIOps",
            "device_ids": "DeviceIDs",
            "kernel_memory_tcp": "KernelMemoryTCP",
            "container_id_file": "ContainerIDFile",
            "uts_mode": "UTSMode",
            "root_fs": "RootFS",
            "enable_ipv6": "EnableIPv6",
            "ipv4_address": "IPv4Address",
            "ipv6_address": "IPv6Address",
            "ipam": "IPAM",
            "tls_info": "TLSInfo",
            "virtual_ips": "VirtualIPs",
        }
        return special_cases[string]
    except KeyError:
        return "".join(title_if_necessary(x) for x in string.split("_"))


class DockerCamelModel(pydantic.BaseModel):
    class Config:
        alias_generator = to_docker_camel
        allow_population_by_field_name = True


def run(
    args: List[Any],
    capture_stdout: bool = True,
    capture_stderr: bool = True,
    input: bytes = None,
    return_stderr: bool = False,
    env: Dict[str, str] = {},
    tty: bool = False,
) -> Union[str, Tuple[str, str]]:
    args = [str(x) for x in args]
    subprocess_env = dict(os.environ)
    subprocess_env.update(env)
    if args[1] == "buildx":
        subprocess_env["DOCKER_CLI_EXPERIMENTAL"] = "enabled"
    if tty:
        stdout_dest = sys.stdout
    elif capture_stdout:
        stdout_dest = subprocess.PIPE
    else:
        stdout_dest = None
    if tty:
        stderr_dest = sys.stderr
    elif capture_stderr:
        stderr_dest = subprocess.PIPE
    else:
        stderr_dest = None
    if os.environ.get("PYTHON_ON_WHALES_DEBUG", "0") == "1":
        print("------------------------------")
        print("command: " + " ".join(args))
        print(f"Env: {subprocess_env}")
        print("------------------------------")
    completed_process = subprocess.run(
        args, input=input, stdout=stdout_dest, stderr=stderr_dest, env=subprocess_env
    )

    if completed_process.returncode != 0:
        if completed_process.stderr is not None:
            if "no such image" in completed_process.stderr.decode().lower():
                raise NoSuchImage(
                    args,
                    completed_process.returncode,
                    completed_process.stdout,
                    completed_process.stderr,
                )
            if "no such service" in completed_process.stderr.decode().lower():
                raise NoSuchService(
                    args,
                    completed_process.returncode,
                    completed_process.stdout,
                    completed_process.stderr,
                )
            if "no such container" in completed_process.stderr.decode().lower():
                raise NoSuchContainer(
                    args,
                    completed_process.returncode,
                    completed_process.stdout,
                    completed_process.stderr,
                )
            if (
                "this node is not a swarm manager"
                in completed_process.stderr.decode().lower()
            ):
                raise NotASwarmManager(
                    args,
                    completed_process.returncode,
                    completed_process.stdout,
                    completed_process.stderr,
                )
            if "no such volume" in completed_process.stderr.decode().lower():
                raise NoSuchVolume(
                    args,
                    completed_process.returncode,
                    completed_process.stdout,
                    completed_process.stderr,
                )

        raise DockerException(
            args,
            completed_process.returncode,
            completed_process.stdout,
            completed_process.stderr,
        )

    if return_stderr:
        return (
            post_process_stream(completed_process.stdout),
            post_process_stream(completed_process.stderr),
        )
    else:
        return post_process_stream(completed_process.stdout)


def post_process_stream(stream: Optional[bytes]):
    if stream is None:
        return ""
    stream = stream.decode()
    if len(stream) != 0 and stream[-1] == "\n":
        stream = stream[:-1]
    return stream


ValidPath = Union[str, Path]


def to_list(x) -> list:
    if isinstance(x, list):
        return x
    else:
        return [x]


# backport of https://docs.python.org/3.9/library/stdtypes.html#str.removesuffix
def removesuffix(string: str, suffix: str) -> str:
    if string.endswith(suffix):
        return string[: -len(suffix)]
    else:
        return string


def removeprefix(string: str, prefix: str) -> str:
    if string.startswith(prefix):
        return string[len(prefix) :]
    else:
        return string


def reader(pipe, pipe_name, queue):
    try:
        with pipe:
            for line in iter(pipe.readline, b""):
                queue.put((pipe_name, line))
    finally:
        queue.put(None)


def stream_stdout_and_stderr(
    full_cmd: list, env: Dict[str, str] = None
) -> Iterable[Tuple[str, bytes]]:
    if env is None:
        subprocess_env = None
    else:
        subprocess_env = dict(os.environ)
        subprocess_env.update(env)

    full_cmd = list(map(str, full_cmd))
    process = Popen(full_cmd, stdout=PIPE, stderr=PIPE, env=subprocess_env)
    q = Queue()
    full_stderr = b""  # for the error message
    # we use deamon threads to avoid hanging if the user uses ctrl+c
    th = Thread(target=reader, args=[process.stdout, "stdout", q])
    th.daemon = True
    th.start()
    th = Thread(target=reader, args=[process.stderr, "stderr", q])
    th.daemon = True
    th.start()
    for _ in range(2):
        for source, line in iter(q.get, None):
            yield source, line
            if source == "stderr":
                full_stderr += line

    exit_code = process.wait()
    if exit_code != 0:
        raise DockerException(full_cmd, exit_code, stderr=full_stderr)


def format_dict_for_cli(dictionary: Dict[str, str], separator="="):
    return [f"{key}{separator}{value}" for key, value in dictionary.items()]


def read_env_file(env_file: Path) -> Dict[str, str]:
    result_dict = {}
    for line in env_file.read_text().splitlines():
        line = line.strip()
        try:
            first_sharp = line.index("#")
        except ValueError:
            pass
        else:
            line = line[:first_sharp]
        if not line:
            continue
        line = line.strip()
        key, value = line.split("=", 1)
        result_dict[key] = value
    return result_dict


def read_env_files(env_files: List[Path]) -> Dict[str, str]:
    result_dict = {}
    for file in env_files:
        result_dict.update(read_env_file(file))
    return result_dict


def all_fields_optional(cls):
    """Decorator function used to modify a pydantic model's fields to all be optional."""
    for field in cls.__fields__.values():
        field.required = False
        field.allow_none = True
    return cls


def format_time_arg(time_object):
    if time_object is None:
        return None
    else:
        return format_time_for_docker(time_object)


def format_time_for_docker(time_object: Union[datetime, timedelta]) -> str:
    if isinstance(time_object, datetime):
        return time_object.strftime("%Y-%m-%dT%H:%M:%S")
    elif isinstance(time_object, timedelta):
        return f"{time_object.total_seconds()}s"
