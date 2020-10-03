# Python on whales!

![alt text](logo.png "Title")

An awesome Python wrapper for an awesome Docker CLI!

Works on Linux, MacOS and Windows, for Python 3.7 and above. 

The docs can be found at this address: <https://gabrieldemarmiesse.github.io/python-on-whales/>

The Github repo can be found at this adress: <https://github.com/gabrieldemarmiesse/python-on-whales>


### Some cool examples:

```python
>>> from python_on_whales import docker

>>> output = docker.run("hello-world")
>>> print(output)

Hello from Docker!
This message shows that your installation appears to be working correctly.

...
```


```python
>>> from python_on_whales import docker
>>> print(docker.run("nvidia/cuda:11.0-base", "nvidia-smi", gpus="all"))
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 450.51.06    Driver Version: 450.51.06    CUDA Version: 11.0     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                               |                      |               MIG M. |
|===============================+======================+======================|
|   0  Tesla T4            On   | 00000000:00:1E.0 Off |                    0 |
| N/A   34C    P8     9W /  70W |      0MiB / 15109MiB |      0%      Default |
|                               |                      |                  N/A |
+-------------------------------+----------------------+----------------------+

+-----------------------------------------------------------------------------+
| Processes:                                                                  |
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |
|        ID   ID                                                   Usage      |
|=============================================================================|
|  No running processes found                                                 |
+-----------------------------------------------------------------------------+
```

```python
>>> from python_on_whales import docker
>>> my_docker_image = docker.pull("ubuntu:20.04")
20.04: Pulling from library/ubuntu
e6ca3592b144: Downloading [=============>                                     ]  7.965MB/28.56MB
534a5505201d: Download complete
990916bd23bb: Download complete

>>> print(my_docker_image.repo_tags)
['ubuntu:20.04']

>>> my_docker_image.remove()
```

```python
>>> from python_on_whales import docker
>>> my_image = docker.build(".", tags="some_name")  # uses Buildx/buildkit by default
[+] Building 1.6s (17/17) FINISHED
 => [internal] load build definition from Dockerfile                                                            0.0s
 => => transferring dockerfile: 32B                                                                             0.0s
 => [internal] load .dockerignore                                                                               0.0s
 => => transferring context: 2B                                                                                 0.0s
 => [internal] load metadata for docker.io/library/python:3.6                                                   1.4s
 => [python_dependencies 1/5] FROM docker.io/library/python:3.6@sha256:29328c59adb9ee6acc7bea8eb86d0cb14033c85  0.0s
 => [internal] load build context                                                                               0.1s
 => => transferring context: 72.86kB                                                                            0.0s
 => CACHED [python_dependencies 2/5] RUN pip install typeguard pydantic requests tqdm                           0.0s
 => CACHED [python_dependencies 3/5] COPY tests/test-requirements.txt /tmp/                                     0.0s
 => CACHED [python_dependencies 4/5] COPY requirements.txt /tmp/                                                0.0s
 => CACHED [python_dependencies 5/5] RUN pip install -r /tmp/test-requirements.txt -r /tmp/requirements.txt     0.0s
 => CACHED [tests_ubuntu_install_without_buildx 1/7] RUN apt-get update &&     apt-get install -y       apt-tr  0.0s
 => CACHED [tests_ubuntu_install_without_buildx 2/7] RUN curl -fsSL https://download.docker.com/linux/ubuntu/g  0.0s
 => CACHED [tests_ubuntu_install_without_buildx 3/7] RUN add-apt-repository    "deb [arch=amd64] https://downl  0.0s
 => CACHED [tests_ubuntu_install_without_buildx 4/7] RUN  apt-get update &&      apt-get install -y docker-ce-  0.0s
 => CACHED [tests_ubuntu_install_without_buildx 5/7] WORKDIR /python-on-whales                                  0.0s
 => CACHED [tests_ubuntu_install_without_buildx 6/7] COPY . .                                                   0.0s
 => CACHED [tests_ubuntu_install_without_buildx 7/7] RUN pip install -e .                                       0.0s
 => exporting to image                                                                                          0.1s
 => => exporting layers                                                                                         0.0s
 => => writing image sha256:e1c2382d515b097ebdac4ed189012ca3b34ab6be65ba0c650421ebcac8b70a4d                    0.0s
 => => naming to docker.io/library/some_image_name
```


### What is it?

Python on Whales is a Docker client for Python. 

* 1 to 1 mapping between the CLI interface and the Python API. No need to look in the docs
what is the name of the function/argument you need.
* Support for the latest Docker features: 
[Docker buildx/buildkit](https://github.com/docker/buildx), 
`docker run --gpu=all ...`
* Support for Docker stack, services and Swarm (same API as the command line).
* Progress bars and progressive outputs when pulling, pushing, loading, building...
* Support for some other CLI commands that are not in Docker-py: 
`docker cp`, `docker run --cpus ...` and more.
* Nice SSH support for remote daemons.
* Docker object as Python objects: Container, Images, Volumes, Services... and their
attributes are updated in real-time!
* A fully typed API compatible with `pathlib` and `os.path`

### Why another project? Why not build on Docker-py?

Two major differences do not permit that:

1) The API is quite different. The aim of Python on Whales is to provide a 1-to-1 
mapping between the Docker command line and Python, so that users don't even have 
to open the docs to do write code.

2) While Docker-py is a complete re-implementation of the Docker client binary 
(written in Go), Python on Whales sits on top of the Docker client binary, which makes 
implementing new features much easier. For example, it's 
[unlikely that docker-py supports Buildx/buildkit](https://github.com/docker/docker-py/issues/2230#issuecomment-454344497)
anytime soon because reimplementing is hard work.
