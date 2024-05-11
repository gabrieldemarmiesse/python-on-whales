import os
import signal
import subprocess
import sys
from datetime import datetime, timedelta
from importlib.metadata import version
from pathlib import Path
from queue import Queue
from subprocess import PIPE, Popen
from threading import Thread
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union, overload

import pydantic
from typing_extensions import Literal

from python_on_whales.exceptions import (
    DockerException,
    NoSuchContainer,
    NoSuchImage,
    NoSuchPod,
    NoSuchService,
    NoSuchVolume,
    NotASwarmManager,
)

PROJECT_ROOT = Path(__file__).parents[1]
PYDANTIC_V2 = version("pydantic").startswith("2.")


def custom_parse_object_as(type_, obj: Any):
    if PYDANTIC_V2:
        return pydantic.TypeAdapter(type_).validate_python(obj)
    else:
        return pydantic.parse_obj_as(type_, obj)


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
            "link_local_ipv6_prefix_length": "LinkLocalIPv6PrefixLen",
            "secondary_ipv6_addresses": "SecondaryIPv6Addresses",
            "endpoint_id": "EndpointID",
            "global_ipv6_prefix_length": "GlobalIPv6PrefixLen",
            "ip_prefix_length": "IPPrefixLen",
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
            "infra_container_id": "InfraContainerID",
        }
        return special_cases[string]
    except KeyError:
        return "".join(title_if_necessary(x) for x in string.split("_"))


class DockerCamelModel(pydantic.BaseModel):
    if PYDANTIC_V2:
        model_config = pydantic.ConfigDict(
            populate_by_name=True,
            alias_generator=to_docker_camel,
        )
    else:

        class Config:
            alias_generator = to_docker_camel
            allow_population_by_field_name = True


@overload
def run(
    args: List[Any],
    capture_stdout: bool = ...,
    capture_stderr: bool = ...,
    input: bytes = ...,
    return_stderr: Literal[True] = ...,
    env: Dict[str, str] = ...,
    tty: bool = ...,
    pass_fds: Sequence[int] = ...,
) -> Tuple[str, str]:
    ...


@overload
def run(
    args: List[Any],
    capture_stdout: bool = ...,
    capture_stderr: bool = ...,
    input: bytes = ...,
    return_stderr: Literal[False] = ...,
    env: Dict[str, str] = ...,
    tty: bool = ...,
    pass_fds: Sequence[int] = ...,
) -> str:
    ...


def run(
    args: List[Any],
    capture_stdout: bool = True,
    capture_stderr: bool = True,
    input: Optional[bytes] = None,
    return_stderr: bool = False,
    env: Dict[str, str] = {},
    tty: bool = False,
    pass_fds: Sequence[int] = (),
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
        args,
        input=input,
        stdout=stdout_dest,
        stderr=stderr_dest,
        env=subprocess_env,
        pass_fds=pass_fds,
    )

    if completed_process.returncode != 0:
        if completed_process.stderr is not None:
            decoded_stderr = completed_process.stderr.decode().lower()
            if "no such image" in decoded_stderr or "image not known" in decoded_stderr:
                raise NoSuchImage(
                    args,
                    completed_process.returncode,
                    completed_process.stdout,
                    completed_process.stderr,
                )
            if "no such service" in decoded_stderr or (
                "service" in decoded_stderr and "not found" in decoded_stderr
            ):
                raise NoSuchService(
                    args,
                    completed_process.returncode,
                    completed_process.stdout,
                    completed_process.stderr,
                )
            if "no such container" in decoded_stderr:
                raise NoSuchContainer(
                    args,
                    completed_process.returncode,
                    completed_process.stdout,
                    completed_process.stderr,
                )
            if "no such pod" in decoded_stderr:
                raise NoSuchPod(
                    args,
                    completed_process.returncode,
                    completed_process.stdout,
                    completed_process.stderr,
                )
            if "this node is not a swarm manager" in decoded_stderr:
                raise NotASwarmManager(
                    args,
                    completed_process.returncode,
                    completed_process.stdout,
                    completed_process.stderr,
                )
            if "no such volume" in decoded_stderr:
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
ValidPortMapping = Union[
    Tuple[Union[str, int], Union[str, int]],
    Tuple[Union[str, int], Union[str, int], str],
]


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
    full_cmd: list, env: Dict[str, str] = None, pass_fds: Sequence[int] = ()
) -> Iterable[Tuple[str, bytes]]:
    if env is None:
        subprocess_env = None
    else:
        subprocess_env = dict(os.environ)
        subprocess_env.update(env)

    full_cmd = list(map(str, full_cmd))
    process = Popen(
        full_cmd, stdout=PIPE, stderr=PIPE, env=subprocess_env, pass_fds=pass_fds
    )
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


def format_time_arg(time_object):
    if time_object is None:
        return None
    else:
        return format_time_for_docker(time_object)


def format_time_for_docker(time_object: Union[datetime, timedelta]) -> str:
    if isinstance(time_object, datetime):
        return time_object.isoformat()
    elif isinstance(time_object, timedelta):
        return f"{time_object.total_seconds()}s"


def format_signal_arg(signal_object: Optional[Union[int, str]]) -> Optional[str]:
    if signal_object is None:
        return None
    else:
        return format_signal_for_docker(signal_object)


def format_signal_for_docker(signal_object: Union[int, str]) -> str:
    if isinstance(signal_object, int):
        return signal.Signals(signal_object).name
    elif isinstance(signal_object, str):
        if hasattr(signal.Signals, "SIG" + signal_object):
            return "SIG" + signal_object
        else:
            return signal_object
    else:
        raise TypeError(f"Got unexpected signal type {type(signal_object).__name__!r}")


def format_port_arg(port_object: ValidPortMapping) -> str:
    if len(port_object) == 1:
        return port_object[0]
    elif len(port_object) == 2:
        return f"{port_object[0]}:{port_object[1]}"
    elif len(port_object) == 3:
        return f"{port_object[0]}:{port_object[1]}/{port_object[2]}"
    else:
        raise ValueError(
            "The size of the tuples in the publish list must be 1, 2, or 3"
        )


def parse_ls_status_count(status_output, status) -> int:
    try:
        return int(status_output.split(status + "(")[1].split(")")[0])
    except IndexError:
        return 0


def join_if_not_none(sequence: Optional[list]) -> Optional[str]:
    if sequence is None:
        return None
    sequence = [str(x) for x in sequence]
    return ",".join(sequence)


def to_seconds(duration: Optional[Union[int, timedelta]]) -> Optional[str]:
    if duration is None:
        return None
    if isinstance(duration, timedelta):
        duration = int(duration.total_seconds())
    return f"{duration}s"
