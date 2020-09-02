from docker_cli_wrapper.components.download_binaries import download_from_url


def test_download_from_url(tmp_path):
    url = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png"
    download_from_url(url, tmp_path / "dodo.png")
    assert (tmp_path / "dodo.png").exists()
