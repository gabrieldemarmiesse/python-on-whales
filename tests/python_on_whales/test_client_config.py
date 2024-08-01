import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from python_on_whales import docker
from python_on_whales.client_config import ClientConfig, ParsingError

fake_json_message = {
    "CreatedAt": "2020-10-08T18:32:55Z",
    "Driver": ["dummy", "fake", ["driver"]],
    "Labels": {"com.docker.stack.namespace": "dodo"},
    "Mountpoint": "/var/lib/docker/volumes/dodo_traefik-data/_data",
    "Name": "dodo_traefik-data",
    "Options": None,
    "Scope": "local",
}


def test_pretty_exception_message_and_report(mocker):
    mocker.patch(
        "python_on_whales.components.volume.cli_wrapper.Volume._fetch_inspect_result_json",
        lambda x, y: fake_json_message,
    )
    with pytest.raises(ParsingError) as err:
        docker.volume.inspect("random_volume")
    error_message = str(err.value)

    assert "This is a bug with python-on-whales itself" in error_message

    # we get the path of the json file with the dump of the response.
    for word in error_message.split():
        if ".json" in word:
            break
    else:
        raise IndexError

    assert Path(word).read_text() == json.dumps(fake_json_message, indent=2)


def test_compose_env_file():
    """Test that the deprecated `compose_env_file` gives a warning, and adds the `--env-file` argument to the compose command"""
    with pytest.warns(UserWarning):
        example_env_file_name = "example.env"
        client_config = ClientConfig(compose_env_file=example_env_file_name)
        assert client_config.docker_compose_cmd.count("--env-file") == 1
        # Since we are operating of a list of commands, we first find the index of the `--env-file` argument, then we check that the next argument is the file name.
        index = client_config.docker_compose_cmd.index("--env-file")
        assert client_config.docker_compose_cmd[index + 1] == example_env_file_name


@pytest.mark.parametrize(
    "compose_env_files",
    [
        ["example1.env", "example2.env"],
        ["example1.env"],
    ],
    ids=["multiple_files", "single_file"],
)
def test_compose_env_files(compose_env_files: Sequence[str]):
    """Test that using only `compose_env_files` adds all the files to the command line arguments"""
    client_config = ClientConfig(compose_env_files=compose_env_files)
    # Since we are operating of a list of commands, we first find the indices of the `--env-file` argument, then we check that the next argument is the file name.
    indices = [
        index
        for index, item in enumerate(client_config.docker_compose_cmd)
        if item == "--env-file"
    ]
    assert len(indices) == len(compose_env_files)
    for index, env_file in zip(indices, compose_env_files):
        assert client_config.docker_compose_cmd[index + 1] == env_file


def test_compose_env_files_and_env_file():
    """Test that using both `compose_env_files` and `compose_env_file` gives a warning, and only uses `compose_env_files`"""
    env_files_input = "example1.env"
    env_file_input = "example2.env"

    with pytest.warns(UserWarning):
        client_config = ClientConfig(
            compose_env_files=[env_files_input], compose_env_file=env_file_input
        )
        assert client_config.docker_compose_cmd.count("--env-file") == len(
            [env_files_input]
        )
        # Since we are operating of a list of commands, we first find the index of the `--env-file` argument, then we check that the next argument is the file name.
        index = client_config.docker_compose_cmd.index("--env-file")
        assert client_config.docker_compose_cmd[index + 1] == env_files_input
