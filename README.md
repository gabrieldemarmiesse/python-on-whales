<img src="https://raw.githubusercontent.com/gabrieldemarmiesse/python-on-whales/master/img/full.png" alt="logo" class="responsive" style="width: 80%; height: auto;">

A Docker client for Python, designed to be fun and intuivive!

Works on Linux, MacOS and Windows, for Python 3.7 and above. 

The docs can be found at this address: <https://gabrieldemarmiesse.github.io/python-on-whales/>

The Github repo can be found at this adress: <https://github.com/gabrieldemarmiesse/python-on-whales>


## How to install?

I have put several hundred of hours of work into this project, because I love Docker and  
I hope to make it fun to use from Python. 

I will likely put several hundred of hours more
into Python-on-whales for bugfixes, maintenance and new features!


The 01/05/2021, the source code will be available at <https://github.com/gabrieldemarmiesse/python-on-whales>
with a MIT licence and the packages will be available with `pip install python-on-whales`


Until May 1st 2021, this package is accessible only by sponsors:

1) Go to <https://github.com/sponsors/gabrieldemarmiesse>

2) Pick any tier

3) I'll send you and invitation to access the repository at <https://github.com/gabrieldemarmiesse/python-on-whales> 
 (one hour max, there is no API in Github for sponsors, I can't automate it).

3) Do either `pip install git+ssh://git@github.com/gabrieldemarmiesse/python-on-whales.git` or if 
   you use a `requirements.txt` or a `setup.py`, you can declare Python on whales as a dependency with
   
```python
# setup.py

from setuptools import find_packages, setup

setup(
    name="my-package",
    install_requires=["python-on-whales @ git+ssh://git@github.com/gabrieldemarmiesse/python-on-whales.git"],
    packages=find_packages(),
)
```

```
# requirements.txt
python-on-whales @ git+ssh://git@github.com/gabrieldemarmiesse/python-on-whales.git
other-package-1
other-package-2
...
``` 

## Some cool examples

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
>>> print(docker.run("nvidia/cuda:11.0-base", ["nvidia-smi"], gpus="all"))
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


## Main features

* 1 to 1 mapping between the CLI interface and the Python API. No need to look in the docs
what is the name of the function/argument you need.
* Support for the latest Docker features: 
[Docker buildx/buildkit](https://github.com/docker/buildx), 
`docker run --gpu=all ...`
* Support for Docker stack, services and Swarm (same API as the command line).
* Progress bars and progressive outputs when pulling, pushing, loading, building...
* Support for some other CLI commands that are not in [Docker-py](https://docker-py.readthedocs.io/en/stable/): 
`docker cp`, `docker run --cpus ...` and more.
* Nice SSH support for remote daemons.
* Docker object as Python objects: Container, Images, Volumes, Services... and their
attributes are updated in real-time!
* Each Docker object can be used as a context manager. When getting out of the 
context, the Docker object is removed automatically, even if an exception occurs.
* A fully typed API (Mypy and IDE-friendly) compatible with `pathlib` and `os.path`

## Why another project? Why not build on Docker-py?

In a sense this project is built on top of [Docker-py](https://docker-py.readthedocs.io/en/stable/) 
because the implementation, the organisation and the API is inspired from the project, but the codebases 
could not be the same.

Two major differences do not permit that:

1) The API is quite different. The aim of Python on Whales is to provide a 1-to-1 
mapping between the Docker command line and Python, so that users don't even have 
to open the docs to do write code.

2) While [Docker-py](https://docker-py.readthedocs.io/en/stable/) is a complete re-implementation of the Docker client binary 
(written in Go), Python on whales sits on top of the Docker client binary, which makes 
implementing new features much easier and safer. For example, it's 
[unlikely that docker-py supports Buildx/buildkit](https://github.com/docker/docker-py/issues/2230#issuecomment-454344497)
anytime soon because rewriting a large Go codebase in Python is hard work.


## Where is the project now? Where is it going?

Currently, about 75% of the Docker CLI API is covered. Of course the most used functions 
were done first: docker run, docker pull, docker push, docker build (with buildx), docker volume...

The main parts missing are Docker swarm support, Docker buildx builders management, and a better inspection 
of Docker objects like volumes and images (for Docker containers, the inspection is pretty good).

This project aims at a 100% feature parity between the Docker CLI and Python on whales. 

This includes Docker buildx, Docker app, Docker Swarm, Docker stacks and Docker compose.

You can consider that this software is in beta, some small API changes are still possible.
 