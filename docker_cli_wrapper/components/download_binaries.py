import platform

import requests
from tqdm import tqdm

DOCKER_VERSION = "19.03.12"


TEMPLATE = "https://download.docker.com/{os}/static/stable/{arch}/docker-{version}.tgz"


def download_docker_cli():
    user_os = get_user_os()
    arch = get_arch()
    file_to_download = TEMPLATE.format(os=user_os, arch=arch, version=DOCKER_VERSION)


def download_from_url(url, dst):
    # Streaming, so we can iterate over the response.
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0))
    block_size = 1024  # 1 Kibibyte
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
            "docker-cli-wrapper cannot automatically download the Docker CLI binary "
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
            f"https://github.com/gabrieldemarmiesse/docker-cli-wrapper/issues \n"
            f"and in the meantime, install Docker manually to make docker-cli-wrapper "
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
            f"https://github.com/gabrieldemarmiesse/docker-cli-wrapper/issues "
            f"and make sure to copy past this error message. \n"
            f"In the meantime, install Docker manually on your system."
        )
