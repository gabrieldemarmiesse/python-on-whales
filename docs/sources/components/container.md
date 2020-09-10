### commit


```python
docker.container.commit(container, tag=None, author=None, message=None, pause=True)
```


----

### cp


```python
docker.container.cp(source, destination)
```


----

### create


```python
docker.container.create()
```


----

### diff


```python
docker.container.diff(container)
```


----

### exec


```python
docker.container.exec(container, command, detach=False)
```


----

### export


```python
docker.container.export(container, output=None)
```


----

### inspect


```python
docker.container.inspect(reference)
```


----

### kill


```python
docker.container.kill(containers, signal=None)
```


----

### list


```python
docker.container.list(all=False)
```


----

### logs


```python
docker.container.logs(container)
```


----

### pause


```python
docker.container.pause(containers)
```


----

### prune


```python
docker.container.prune(filters=[])
```


----

### remove


```python
docker.container.remove(containers, force=False, volumes=False)
```


----

### rename


```python
docker.container.rename(container, new_name)
```


----

### restart


```python
docker.container.restart(containers, time=None)
```


----

### run


```python
docker.container.run(
    image,
    command=None,
    *,
    blkio_weight=None,
    cpu_period=None,
    cpu_quota=None,
    cpu_rt_period=None,
    cpu_rt_runtime=None,
    cpu_shares=None,
    cpus=None,
    detach=False,
    envs={},
    env_files=[],
    gpus=None,
    hostname=None,
    ip=None,
    ip6=None,
    ipc=None,
    isolation=None,
    kernel_memory=None,
    log_driver=None,
    mac_address=None,
    memory=None,
    memory_reservation=None,
    memory_swap=None,
    name=None,
    healthcheck=True,
    oom_kill=True,
    pid=None,
    pids_limit=None,
    platform=None,
    privileged=False,
    publish_all=False,
    read_only=False,
    restart=None,
    rm=False,
    runtime=None,
    shm_size=None,
    stop_timeout=None,
    user=None,
    userns=None,
    uts=None,
    volumes=[],
    volume_driver=None,
    workdir=None
)
```


----

### start


```python
docker.container.start(containers)
```


----

### stop


```python
docker.container.stop(containers, time=None)
```


----

