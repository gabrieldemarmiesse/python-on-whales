import platform
import shutil
import tempfile
import warnings
from pathlib import Path

import requests
from tqdm import tqdm

DOCKER_VERSION = "19.03.12"

CACHE_DIR = Path.home() / ".cache" / "python-on-whales"

TEMPLATE = "https://download.docker.com/{os}/static/stable/{arch}/docker-{version}.tgz"
DOCKER_BINARY_PATH = CACHE_DIR / "docker-cli" / DOCKER_VERSION / "docker"


def download_docker_cli() -> Path:
    user_os = get_user_os()
    arch = get_arch()
    file_to_download = TEMPLATE.format(os=user_os, arch=arch, version=DOCKER_VERSION)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        tar_file = tmp_dir / "docker.tgz"
        download_from_url(file_to_download, tar_file)
        extract_dir = tmp_dir / "extracted"
        shutil.unpack_archive(tar_file, extract_dir)

        DOCKER_BINARY_PATH.parent.mkdir(exist_ok=True, parents=True)
        shutil.move(extract_dir / "docker" / "docker", DOCKER_BINARY_PATH)

    warnings.warn(
        f"The docker client binary file {DOCKER_VERSION} was downloaded and put "
        f"in `{DOCKER_BINARY_PATH.absolute()}`. \n"
        f"You can feel free to remove it if you wish, Python on whales will download "
        f"it again if needed."
    )
    return DOCKER_BINARY_PATH


def download_from_url(url, dst):
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
        print("ERROR, something went wrong")


def get_user_os():
    user_os = platform.system()
    if user_os == "Linux":
        return "linux"
    elif user_os == "Darwin":
        return "mac"
    elif user_os == "Windows":
        raise NotImplementedError(
            "python-on-whales cannot automatically download the Docker CLI binary "
            "file because there is no binary available for Windows at "
            "https://download.docker.com/ . \n"
            "Please install Docker Desktop for Windows. "
            "You can find the instructions here:  \n"
            "https://docs.docker.com/docker-for-windows/install/"
        )
    else:
        raise NotImplementedError(
            f"Unknown OS: {user_os}, cannot determine which Docker CLI binary file to "
            f"download. \n"
            f"Please open an issue at \n"
            f"https://github.com/gabrieldemarmiesse/python-on-whales/issues \n"
            f"and in the meantime, install Docker manually to make python-on-whales "
            f"work."
        )


def get_arch():
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
