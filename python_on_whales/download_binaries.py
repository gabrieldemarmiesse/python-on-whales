__all__ = ("download_docker_cli", "get_docker_binary_path_in_cache")

import platform
import shutil
import tempfile
import warnings
from pathlib import Path

import requests
from tqdm import tqdm

DOCKER_VERSION = "20.10.5"
BUILDX_VERSION = "0.5.1"

CACHE_DIR = Path.home() / ".cache" / "python-on-whales"

TEMPLATE_CLI = (
    "https://download.docker.com/{os}/static/stable/{arch}/docker-{version}.tgz"
)
WINDOWS_CLI_URL = "https://github.com/StefanScherer/docker-cli-builder/releases/download/{version}/docker.exe"


def get_docker_binary_path_in_cache():
    return CACHE_DIR / "docker-cli" / DOCKER_VERSION / "docker"


def get_docker_cli_url():
    user_os = get_user_os()
    if user_os == "windows":
        return WINDOWS_CLI_URL.format(version=DOCKER_VERSION)
    arch = get_arch_for_docker_cli_url()
    return TEMPLATE_CLI.format(os=user_os, arch=arch, version=DOCKER_VERSION)


def download_docker_cli():
    warnings.warn(
        "Downloading the docker client with python-on-whales is being "
        "deprecated, and this functionality will be removed in v1.0. "
        "See https://github.com/gabrieldemarmiesse/python-on-whales/issues/556 "
        "for planned v1.0 changes.",
        DeprecationWarning,
    )
    file_to_download = get_docker_cli_url()

    extension = file_to_download.split(".")[-1]
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        downloaded_file_path = tmp_dir / f"docker.{extension}"
        download_from_url(file_to_download, downloaded_file_path)

        docker_binary_path = get_docker_binary_path_in_cache()
        docker_binary_path.parent.mkdir(exist_ok=True, parents=True)

        if extension == "tgz":
            extract_dir = tmp_dir / "extracted"
            shutil.unpack_archive(str(downloaded_file_path), str(extract_dir))
            shutil.move(extract_dir / "docker" / "docker", docker_binary_path)
        elif extension == "exe":
            shutil.move(downloaded_file_path, docker_binary_path)

    warnings.warn(
        f"The docker client binary file {DOCKER_VERSION} was downloaded and put "
        f"in `{docker_binary_path.absolute()}`. \n"
        f"You can feel free to remove it if you wish, Python on whales will download "
        f"it again if needed."
    )


def download_from_url(url, dst):
    try:
        _download_from_url(url, dst)
    except Exception as e:
        raise ConnectionError(f"Error while downloading {url}") from e


def _download_from_url(url, dst):
    # Streaming, so we can iterate over the response.
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0))
    block_size = 1024
    progress_bar = tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True)
    with open(dst, "wb") as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        raise ConnectionError(
            f"Total size should be {total_size_in_bytes}, downloaded {progress_bar.n}"
        )


def get_user_os():
    user_os = platform.system()
    if user_os == "Linux":
        return "linux"
    elif user_os == "Darwin":
        return "mac"
    elif user_os == "Windows":
        return "windows"
    else:
        raise NotImplementedError(
            f"Unknown OS: {user_os}, cannot determine which Docker CLI binary file to "
            f"download. \n"
            f"Please open an issue at \n"
            f"https://github.com/gabrieldemarmiesse/python-on-whales/issues \n"
            f"and in the meantime, install Docker manually to make python-on-whales "
            f"work."
        )


def get_arch_for_docker_cli_url():
    arch = platform.architecture()[0]

    # I don't know the exact list of possible architectures,
    # so if a user reports a NotImplementedError, we can easily add
    # his/her platform here.
    arch_mapping = {
        "NotImplementedError": "aarch64",
        "NotImplementedError2": "armel",
        "NotImplementedError3": "armhf",
        "NotImplementedError4": "ppc64le",
        "NotImplementedError5": "s390x",
        "64bit": "x86_64",
    }

    try:
        return arch_mapping[arch]
    except KeyError:
        raise NotImplementedError(
            f"The architecture detected on your system is `{arch}`, the list of "
            f"available architectures is {list(arch_mapping.values())}. \n"
            f"Please open an issue at \n"
            f"https://github.com/gabrieldemarmiesse/python-on-whales/issues "
            f"and make sure to copy past this error message. \n"
            f"In the meantime, install Docker manually on your system."
        )
