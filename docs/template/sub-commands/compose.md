## Some notes about the compose functions

Behind the scenes, 
the [Go implementation of Docker compose](https://github.com/docker/compose-cli)
is called, not the [Python implementation](https://github.com/docker/compose).

The Go implementation of compose is still experimental, so take the appropriate precautions.

If you don't need to set any project-wide options, like the project name or 
the compose file path, you can just import `docker` and start working.

```python
from python_on_whales import docker

docker.compose.build()
docker.compose.up()
...
docker.compose.down()
```

Otherwise, you have to define your project-wide options only once, when creating the Docker client.

```python
from python_on_whales import DockerClient

docker = DockerClient(compose_files=["./my-compose-file.yml"])

docker.compose.build()
docker.compose.up()
...
docker.compose.down()
```


{{autogenerated}}
