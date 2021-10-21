from pathlib import Path

import pytest

from python_on_whales import docker
from python_on_whales.client_config import ParsingError

fake_json_message = """
[
    {
        "CreatedAt": "2020-10-08T18:32:55Z",
        "Driver": ["dummy", "fake", ["driver"]],
        "Labels": {
            "com.docker.stack.namespace": "dodo"
        },
        "Mountpoint": "/var/lib/docker/volumes/dodo_traefik-data/_data",
        "Name": "dodo_traefik-data",
        "Options": null,
        "Scope": "local"
    }
]
"""


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

    assert Path(word).read_text() == fake_json_message
