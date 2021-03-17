import os
import platform
import shutil
import stat
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
TEMPLATE_BUILDX = "https://github.com/docker/buildx/releases/download/v{version}/buildx-v{version}.{os}-{arch}"


DOCKER_BINARY_PATH = CACHE_DIR / "docker-cli" / DOCKER_VERSION / "docker"
BUILDX_BINARY_PATH = Path.home() / ".docker" / "cli-plugins" / "docker-buildx"


def get_docker_cli_url():
    user_os = get_user_os()
    if user_os == "windows":
        return WINDOWS_CLI_URL.format(version=DOCKER_VERSION)
    arch = get_arch_for_docker_cli_url()
    return TEMPLATE_CLI.format(os=user_os, arch=arch, version=DOCKER_VERSION)


def get_buildx_url():
    user_os = platform.system().lower()
    arch = get_arch_for_buildx_url()
    url = TEMPLATE_BUILDX.format(version=BUILDX_VERSION, os=user_os, arch=arch)
    if user_os == "windows":
        url += ".exe"
    return url


def download_buildx():
    BUILDX_BINARY_PATH.parent.mkdir(exist_ok=True, parents=True)
    download_from_url(get_buildx_url(), BUILDX_BINARY_PATH)

    st = os.stat(BUILDX_BINARY_PATH)
    os.chmod(BUILDX_BINARY_PATH, st.st_mode | stat.S_IEXEC)
    warnings.warn(
        f"The docker buildx binary file {BUILDX_VERSION} was downloaded and put "
        f"in `{BUILDX_BINARY_PATH.absolute()}`. \n"
        f"You can feel free to remove it if you wish, Python on whales will download "
        f"it again if needed."
    )


def download_docker_cli():
    file_to_download = get_docker_cli_url()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        tar_file = tmp_dir / "docker.tgz"
        download_from_url(file_to_download, tar_file)
        extract_dir = tmp_dir / "extracted"
        shutil.unpack_archive(str(tar_file), str(extract_dir))

        DOCKER_BINARY_PATH.parent.mkdir(exist_ok=True, parents=True)
        shutil.move(extract_dir / "docker" / "docker", DOCKER_BINARY_PATH)

    warnings.warn(
        f"The docker client binary file {DOCKER_VERSION} was downloaded and put "
        f"in `{DOCKER_BINARY_PATH.absolute()}`. \n"
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


def get_arch_for_buildx_url():
    arch = platform.architecture()[0]

    # I don't know the exact list of possible architectures,
    # so if a user reports a NotImplementedError, we can easily add
    # his/her platform here.
    arch_mapping = {
        "NotImplementedError": "arm-v6",
        "NotImplementedError2": "arm-v7",
        "NotImplementedError3": "arm64",
        "NotImplementedError4": "ppc64le",
        "NotImplementedError5": "s390x",
        "64bit": "amd64",
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
            f"In the meantime, install Docker buildx manually on your system: \n"
            f"https://github.com/docker/buildx"
        )
