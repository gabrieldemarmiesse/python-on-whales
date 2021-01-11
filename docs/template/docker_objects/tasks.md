# Docker tasks

Tasks in Docker swarm

Don't use the constructor directly. Instead use 
```python
from python_on_whales import docker

my_docker_task = docker.task.inspect("some-task-id")

my_tasks_list = docker.service.ps("my-service")

```
For type hints, use this

```python
from python_on_whales import Task

def print_creation_time(some_task: Task):
    print(some_task.created_at)
```


## Attributes

It attributes are the same that you get with the command line:
`docker inspect <task-id>`

To get a complete description of those attributes, you 
can take a look at the [daemon api reference page](https://docs.docker.com/engine/api/v1.40/#operation/TaskInspect) 
and click on "200 No error".
