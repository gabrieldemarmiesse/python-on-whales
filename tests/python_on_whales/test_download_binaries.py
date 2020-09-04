from python_on_whales import download_binaries
from python_on_whales.utils import run


def test_download_from_url(tmp_path):
    url = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png"
    download_binaries.download_from_url(url, tmp_path / "dodo.png")
    assert (tmp_path / "dodo.png").exists()


def test_download_cli():
    try:
        download_binaries.DOCKER_BINARY_PATH.unlink()
    except FileNotFoundError:
        pass
    download_binaries.download_docker_cli()
    simple_command = [
        download_binaries.DOCKER_BINARY_PATH,
        "run",
        "--rm",
        "hello-world",
    ]
    output = run(simple_command, capture_stdout=True, capture_stderr=True)
    assert "Hello from Docker!" in output


def test_download_cli_from_cli():
    try:
        download_binaries.DOCKER_BINARY_PATH.unlink()
    except FileNotFoundError:
        pass
    run(["python-on-whales", "download-cli"])
    simple_command = [
        download_binaries.DOCKER_BINARY_PATH,
        "run",
        "--rm",
        "hello-world",
    ]
    output = run(simple_command, capture_stdout=True, capture_stderr=True)
    assert "Hello from Docker!" in output
