# Images

Don't use the constructor directly. Instead use 
```python
from python_on_whales import docker

my_docker_image = docker.image.inspect("my-image-name")

# or

my_docker_image = docker.pull("my-image-name")
```
For type hints, use this

```python
from python_on_whales import docker, Image

def print_dodo(image: Image):
    print(docker.run(image, ["echo", "dodo"]))
```


## Attributes

It attributes are the same that you get with the command line:
`docker image inspect ...`

An example is worth many lines of descriptions.

```
In [1]: from python_on_whales import docker

In [2]: image = docker.pull("ubuntu")
20.04: Pulling from library/ubuntu
6a5697faee43: Pull complete
ba13d3bc422b: Pull complete
a254829d9e55: Pull complete
Digest: sha256:fff16eea1a8ae92867721d90c59a75652ea66d29c05294e6e2f898704bdb8cf1
Status: Downloaded newer image for ubuntu:latest
docker.io/library/ubuntu:latest

In [3]: def super_print(obj):
   ...:     print(f"type={type(obj)}, value={obj}")
   ...:

In [4]: super_print(image.id)
type = <class 'str'>, value = sha256:f643c72bc25212974c16f3348b3a898b1ec1eb13ec1539e10a103e6e217eb2f1

In [5]: super_print(image.repo_tags)
type = <class 'list'>, value = ['ubuntu:latest']

In [6]: super_print(image.repo_digests)
type = <class 'list'>, value = ['ubuntu@sha256:c95a8e48bf88e9849f3e0f723d9f49fa12c5a00cfc6e60d2bc99d87555295e4c']

In [7]: super_print(image.parent)
type = <class 'str'>, value = 

In [8]: super_print(image.comment)
type = <class 'str'>, value = 

In [9]: super_print(image.created)
type = <class 'datetime.datetime'>, value = 2020-11-25 22:25:29.546718+00:00

In [10]: super_print(image.container)
type = <class 'str'>, value = 0672cd8bc2236c666c647f97effe707c8f6ba9783da7e88763c8d46c69dc174a

In [11]: super_print(image.container_config)
type = <class 'python_on_whales.components.container.ContainerConfig'>, value = hostname='0672cd8bc223' domainname='' user='' attach_stdin=False attach_stdout=False attach_stderr=False exposed_ports=None tty=False open_stdin=False stdin_once=False env=['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'] cmd=['/bin/sh', '-c', '#(nop) ', 'CMD ["/bin/bash"]'] healthcheck=None args_escaped=None image='sha256:28e90b4e135b38b4dd5efd0045019a2c8bfb7e114383e3a4ae80b1ec0dcaaf79' volumes=None working_dir=PosixPath('.') entrypoint=None network_disabled=None mac_address=None on_build=None labels={} stop_signal=None stop_timeout=None shell=None

In [12]: super_print(image.docker_version)
type = <class 'str'>, value = 19.03.12

In [13]: super_print(image.author)
type = <class 'str'>, value = 

In [14]: super_print(image.config)
type = <class 'python_on_whales.components.container.ContainerConfig'>, value = hostname='' domainname='' user='' attach_stdin=False attach_stdout=False attach_stderr=False exposed_ports=None tty=False open_stdin=False stdin_once=False env=['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'] cmd=['/bin/bash'] healthcheck=None args_escaped=None image='sha256:28e90b4e135b38b4dd5efd0045019a2c8bfb7e114383e3a4ae80b1ec0dcaaf79' volumes=None working_dir=PosixPath('.') entrypoint=None network_disabled=None mac_address=None on_build=None labels=None stop_signal=None stop_timeout=None shell=None

In [15]: super_print(image.architecture)
type = <class 'str'>, value = amd64

In [16]: super_print(image.os)
type = <class 'str'>, value = linux

In [17]: super_print(image.os_version)
type = <class 'NoneType'>, value = None

In [18]: super_print(image.size)
type = <class 'int'>, value = 72898198

In [19]: super_print(image.virtual_size)
type = <class 'int'>, value = 72898198

In [20]: super_print(image.graph_driver.name)
type = <class 'str'>, value = overlay2

In [21]: super_print(image.graph_driver.data)
type = <class 'dict'>, value = {'LowerDir': '/var/lib/docker/overlay2/9cb13ec06b26811bb6ad55246f1e5c39d48f8cc5f31ab800272604cfb4ffc453/diff:/var/lib/docker/overlay2/b96f59d6f7a2869dc030b79bbf4883884ba1f2dc79d00c454322cffc62f92f48/diff', 'MergedDir': '/var/lib/docker/overlay2/559f32baec3b986c62354f959b143b6bbcae64d07af7c2be75bcc1e5780643a0/merged', 'UpperDir': '/var/lib/docker/overlay2/559f32baec3b986c62354f959b143b6bbcae64d07af7c2be75bcc1e5780643a0/diff', 'WorkDir': '/var/lib/docker/overlay2/559f32baec3b986c62354f959b143b6bbcae64d07af7c2be75bcc1e5780643a0/work'}

In [22]: super_print(image.root_fs.type)
type = <class 'str'>, value = layers

In [23]: super_print(image.root_fs.layers)
type = <class 'list'>, value = ['sha256:bacd3af13903e13a43fe87b6944acd1ff21024132aad6e74b4452d984fb1a99a', 'sha256:9069f84dbbe96d4c50a656a05bbe6b6892722b0d1116a8f7fd9d274f4e991bf6', 'sha256:f6253634dc78da2f2e3bee9c8063593f880dc35d701307f30f65553e0f50c18c']

In [24]: super_print(image.root_fs.base_layer)
type = <class 'NoneType'>, value = None

In [25]: super_print(image.metadata)
type = <class 'dict'>, value = {'LastTagTime': '0001-01-01T00:00:00Z'}
```

{{autogenerated}}


