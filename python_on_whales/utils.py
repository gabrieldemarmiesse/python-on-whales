import subprocess
import warnings
from pathlib import Path
from queue import Queue
from subprocess import PIPE, Popen
from threading import Thread
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import pydantic

from python_on_whales.download_binaries import download_buildx

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
            "ip_adress": "IPAddress",
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


class DockerException(Exception):
    def __init__(
        self,
        command_launched: List[str],
        return_code: int,
        stdout: Optional[bytes] = None,
        stderr: Optional[bytes] = None,
    ):
        command_launched_str = " ".join(command_launched)
        error_msg = (
            f"The docker command executed was `{command_launched_str}`.\n"
            f"It returned with code {return_code}\n"
        )
        if stdout is not None:
            error_msg += f"The content of stdout is '{stdout.decode()}'\n"
        else:
            error_msg += (
                "The content of stdout can be found above the "
                "stacktrace (it wasn't captured).\n"
            )
        if stderr is not None:
            error_msg += f"The content of stderr is '{stderr.decode()}'\n"
        else:
            error_msg += (
                "The content of stderr can be found above the "
                "stacktrace (it wasn't captured)."
            )
        super().__init__(error_msg)


def run(
    args: List[Any],
    capture_stdout: bool = True,
    capture_stderr: bool = True,
    input: bytes = None,
    return_stderr: bool = False,
    env: Dict[str, str] = {},
) -> Union[str, Tuple[str, str]]:
    args = [str(x) for x in args]
    if args[1] == "buildx":
        install_buildx_if_needed(args[0])
        env["DOCKER_CLI_EXPERIMENTAL"] = "enabled"
    if env == {}:
        env = None
    if capture_stdout:
        stdout_dest = subprocess.PIPE
    else:
        stdout_dest = None
    if capture_stderr:
        stderr_dest = subprocess.PIPE
    else:
        stderr_dest = None
    completed_process = subprocess.run(
        args, input=input, stdout=stdout_dest, stderr=stderr_dest, env=env
    )

    if completed_process.returncode != 0:
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


def install_buildx_if_needed(docker_binary: str):
    completed_process = subprocess.run(
        [docker_binary, "buildx"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"DOCKER_CLI_EXPERIMENTAL": "enabled"},
    )
    if completed_process.returncode == 0:
        return

    stderr = completed_process.stderr.decode()
    if "is not a docker command" in stderr:
        warnings.warn(
            "It seems that docker buildx is not installed on your system. \n"
            "It's going to be downloaded for you. It's only a one time thing."
            "The next calls to the buildx command won't trigger the "
            "download again."
        )
        download_buildx()
    else:
        raise RuntimeError(
            f"It seems buildx is not properly installed. When running "
            f"'docker buildx', here is the result:\n"
            f"{stderr}"
        )


def reader(pipe, pipe_name, queue):
    try:
        with pipe:
            for line in iter(pipe.readline, b""):
                queue.put((pipe_name, line))
    finally:
        queue.put(None)


def stream_stdout_and_stderr(full_cmd: list) -> Iterable[Tuple[str, bytes]]:
    full_cmd = list(map(str, full_cmd))
    process = Popen(full_cmd, stdout=PIPE, stderr=PIPE)
    q = Queue()
    full_stderr = b""  # for the error message
    Thread(target=reader, args=[process.stdout, "stdout", q]).start()
    Thread(target=reader, args=[process.stderr, "stderr", q]).start()
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
        key, value = line.split("=")
        result_dict[key] = value
    return result_dict


def read_env_files(env_files: List[Path]) -> Dict[str, str]:
    result_dict = {}
    for file in env_files:
        result_dict.update(read_env_file(file))
    return result_dict
