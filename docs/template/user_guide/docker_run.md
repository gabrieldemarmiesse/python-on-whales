# The different ways of using docker.run()


## Simple call

```python
from python_on_whales import docker

stdout_as_str = docker.run("hello-world")
print(stdout_as_str)

# Hello from Docker!
# This message shows that your installation appears to be working correctly.
# ...
```

This is the simplest way. The function `docker.run(...)` returns only when the container 
is done and the output (stdout) is returned all at once in a single string.

This is very practical for simple use cases, but not so much when you have a container that
needs to run for a very long time for example, as you don't get the output in real time.

## Detach the container

```python
from python_on_whales import docker
from redis import Redis

redis_container = docker.run("redis", detach=True, publish=[(6379, 6379)])
# the container is up and listening on port 6379

redis_client = Redis()
redis_client.set("hello", "world")
print(redis_client.get("hello"))
# b'world'
```

This is a very simple way to start a container in the background. It will continue running 
until the process inside exits. It's useful when running servers for example, because they should
never stop.


## Detach with the context manager

```python
from python_on_whales import docker
from redis import Redis

with docker.run("redis", detach=True, publish=[(6379, 6379)]) as redis_container:
    # the container is up and listening on port 6379
    redis_client = Redis()
    redis_client.set("hello", "world")
    print(redis_client.get("hello"))
    # b'world'

print("The container is now stopped and removed because we're outside the context manager")
print(redis_container.state.running)  # will raise an error with the message "no such container"
```

Using the context manager is quite useful when you need the container running in the background
but you need to know exactly for how long it will live.

For example in unit tests, you might need a redis server to execute a function. 
You can then have the redis container running only during this specific unit test.

This is also better than calling manually `redis_container.remove()`. Why? 
For the same reason it's better to do `with open(...) as f:` than `f = open(...)`. If an exception occurs 
in the context manager block, the container is still removed.


## Stream the output

```python
from python_on_whales import docker

output_generator = docker.run("busybox", ["ping", "-c", "50", "www.google.com"], stream=True, name="box")

for stream_type, stream_content in output_generator:
    print(f"Stream type: {stream_type}, stream content: {stream_content}")

# Stream type: stdout, stream content: b'PING www.google.com (142.250.74.228): 56 data bytes\n'
# Stream type: stdout, stream content: b'64 bytes from 142.250.74.228: seq=0 ttl=119 time=18.350 ms\n'
# Stream type: stdout, stream content: b'64 bytes from 142.250.74.228: seq=1 ttl=119 time=18.386 ms\n'
# ...
# Stream type: stdout, stream content: b'64 bytes from 142.250.74.228: seq=48 ttl=119 time=18.494 ms\n'
# Stream type: stdout, stream content: b'64 bytes from 142.250.74.228: seq=49 ttl=119 time=18.260 ms\n'
# Stream type: stdout, stream content: b'\n'
# Stream type: stdout, stream content: b'--- www.google.com ping statistics ---\n'
# Stream type: stdout, stream content: b'50 packets transmitted, 50 packets received, 0% packet loss\n'
# Stream type: stdout, stream content: b'round-trip min/avg/max = 17.547/18.075/18.508 ms\n'

# when the generator is done and we're out of the loop
# it means the container has finished running.
print(docker.container.inspect("box").state.running)
# False
```

This is very useful for long running processes. For example if you need the output 
of a container that will stay up for a very long time.