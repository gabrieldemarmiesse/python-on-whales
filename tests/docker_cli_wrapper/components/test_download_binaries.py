from docker_cli_wrapper.components import download_binaries
from docker_cli_wrapper.utils import run


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
