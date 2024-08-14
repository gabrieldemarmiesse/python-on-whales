import json
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence, Tuple

import pytest

from python_on_whales import DockerClient, docker
from python_on_whales.client_config import ClientConfig, ParsingError
from python_on_whales.utils import PROJECT_ROOT

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


@contextmanager
def _create_temp_env_files() -> Iterator[Tuple[Path, Path]]:
    """Creates two temporary env files and yields their paths. The files are deleted after the context manager is exited."""
    path = PROJECT_ROOT / "tests/python_on_whales/components"
    env_file_1 = path / "example1.env"
    with env_file_1.open("w") as f:
        f.write("A=1\n")
        f.write("B=1\n")
    env_file_2 = path / "example2.env"
    with env_file_2.open("w") as f:
        f.write("B=2\n")
    yield env_file_1, env_file_2
    env_file_1.unlink()
    env_file_2.unlink()


def test_run_compose_command_with_env_file():
    """Test that checks the configuration for the compose stack and checks that the env files are loaded correctly

    The docker compose service, `service_using_env_variables`, is defined in `dummy_compose.yml` and uses the env variables `A` and `B`.
    If no env files are provided, the values of `A` and `B` are set to a default value of `0` in the service.
    We check if the values of `A` and `B` are set to the values in the env files.

    The cases tested are:
    * Single env file using the old `compose_env_file` argument
    * Single env file using the new `compose_env_files` argument
    * Multiple env files using the new `compose_env_files` argument
        * Later env files should override the values of earlier env files
        * The order of the env files should matter
    """
    with _create_temp_env_files() as (env_file_1, env_file_2):
        COMPOSE_FILE = (
            PROJECT_ROOT / "tests/python_on_whales/components/dummy_compose.yml"
        )
        SERVICE = "service_using_env_variables"

        # Test with no env-file to check the default values, should be `0`, as is default in the service definition.
        client = DockerClient(compose_files=[COMPOSE_FILE])
        config = client.compose.config()
        environment = config.services[SERVICE].environment
        assert "A" in environment and environment["A"] == "0"
        assert "B" in environment and environment["B"] == "0"

        # Test with single env-file using the old `compose_env_file` argument
        client = DockerClient(
            compose_files=[COMPOSE_FILE],
            compose_env_file=env_file_1,
        )
        config = client.compose.config()
        environment = config.services[SERVICE].environment
        assert "A" in environment and environment["A"] == "1"
        assert "B" in environment and environment["B"] == "1"

        # Test with single env-file using the new `compose_env_files` argument
        client = DockerClient(
            compose_files=[COMPOSE_FILE],
            compose_env_files=[env_file_1],
        )
        config = client.compose.config()
        environment = config.services[SERVICE].environment
        assert "A" in environment and environment["A"] == "1"
        assert "B" in environment and environment["B"] == "1"

        # Test with multiple env-files using the new `compose_env_files` argument.
        # Since `env_file2` is loaded after `env_file1`, the value of `B` should be overridden by `env_file_2`.
        client = DockerClient(
            compose_files=[COMPOSE_FILE],
            compose_env_files=[env_file_1, env_file_2],
        )
        config = client.compose.config()
        environment = config.services[SERVICE].environment
        assert "A" in environment and environment["A"] == "1"
        assert "B" in environment and environment["B"] == "2"

        # Test with multiple env-files using the new `compose_env_files` argument.
        # Since `env_file1` is loaded after `env_file2`, the value of `B` should be overridden by `env_file_1`.
        client = DockerClient(
            compose_files=[COMPOSE_FILE],
            compose_env_files=[env_file_2, env_file_1],
        )
        config = client.compose.config()
        environment = config.services[SERVICE].environment
        assert "A" in environment and environment["A"] == "1"
        assert "B" in environment and environment["B"] == "1"
