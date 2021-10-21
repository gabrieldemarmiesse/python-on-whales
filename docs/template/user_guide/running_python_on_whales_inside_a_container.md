# Running python-on-whales inside a container

*To follow this example, you just need Docker installed, and nothing else!*

### The use case

Sometimes you don't want to install Python on your system, but you still
would like to use python-on-whales to handle most of the Docker logic.

You can then run python-on-whales inside a Docker container. For simplicity,
we let the container access the Docker daemon of the host.

Let's give you the code example, and we'll explain afterwards where is the magic.


### Example

We want to run this small Python script. It uses python-on-whales. We'll call it `main.py`

```python
# main.py
from python_on_whales import docker

print("We are going to run the hello world docker container")

output = docker.run("hello-world")

print("Here is the output:")
print(output)

print(f"buildx version: {docker.buildx.version()}")
print(f"compose version: {docker.compose.version()}")
```

Next to this `main.py`, make a `Dockerfile`.

```Dockerfile
# Dockerfile
FROM python:3.9

RUN pip install python-on-whales
RUN python-on-whales download-cli

# install docker buildx, this step is optional
RUN mkdir -p ~/.docker/cli-plugins/
RUN wget https://github.com/docker/buildx/releases/download/v0.6.3/buildx-v0.6.3.linux-amd64 -O ~/.docker/cli-plugins/docker-buildx
RUN chmod a+x  ~/.docker/cli-plugins/docker-buildx

# install docker compose, this step is optional
RUN mkdir -p ~/.docker/cli-plugins/
RUN wget https://github.com/docker/compose/releases/download/v2.0.1/docker-compose-linux-x86_64 -O ~/.docker/cli-plugins/docker-compose
RUN chmod a+x  ~/.docker/cli-plugins/docker-compose

COPY ./main.py /main.py
CMD python /main.py
```

We're all set! Let's run this Python script, without having Python installed on the system!

```bash
docker build -t image-with-python-on-whales .
docker run -v /var/run/docker.sock:/var/run/docker.sock image-with-python-on-whales
```

You should see this output:

```
We are going to run the hello world docker container
Here is the output:

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
 
buildx version: github.com/docker/buildx v0.6.3 266c0eac611d64fcc0c72d80206aa364e826758d
compose version: Docker Compose version v2.0.0-rc.2
```

### How does it work?

The main magic here is the sharing of the docker socket between the host and the container.
This is done with the `-v /var/run/docker.sock:/var/run/docker.sock`.

With this option, the container can have access to the docker API. But it still needs the binary client in Go.
Download it in the dockerfile with `python-no-whales download-cli`. You can then optionally install buildx and compose.

Then you're good to go! Simple as that.