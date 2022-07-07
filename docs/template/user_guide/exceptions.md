# Capturing exceptions

## Exception classes

Exceptions raised will be an instance of `DockerException`, or a child class for
more specific errors.

Those are the child classes:

* `NoSuchContainer`
* `NoSuchImage`
* `NoSuchService`
* `NotASwarmManager`
* `NoSuchVolume`

All exceptions will have these 4 attributes:

* docker_command: the docker command used internally, as a list of strings.
* return_code: the exit code docker client exited with, as an int
* stdout: the content that docker wrote to stdout, as a string, or `None`
* stderr: the content that docker wrote to stderr, as a string, or `None`

## Example

```python
import logging
from python_on_whales import DockerClient
from python_on_whales.exceptions import DockerException

client = DockerClient(compose_files=["/tmp/docker-compose.yml"])
try:
    client.execute("my-service", ["arg1", "arg2"])
except DockerException as e:
    print(f"Exit code {e.return_code} while running {e.docker_command}")
```
