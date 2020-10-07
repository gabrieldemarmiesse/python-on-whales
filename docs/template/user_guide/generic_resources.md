# Docker Swarm generic resources

There are two kind of generic resources, discreet and named.

Both are declared in `/etc/docker/daemon.json` and both are 
accessible in your containers as environment variables.

## Named resources

Named resources should be used when you have a small number of things you want accessed.
The best example is gpu devices. Each gpu has a UUID, which can be the 
name of this resources. Actually you could also use an index, and this index would have 
to be the "name" of the gpu.

Since we want to show they're generic, let's take something else than GPUs for this example.

Let's say you have 5 hamsters connected to your node, making an app run:

<img src="https://i.imgur.com/6bjNsYU.gif" alt="logo" class="responsive" style="width: 45%; height: auto;">
<img src="https://i.imgur.com/6bjNsYU.gif" alt="logo" class="responsive" style="width: 45%; height: auto;">
<img src="https://i.imgur.com/6bjNsYU.gif" alt="logo" class="responsive" style="width: 30%; height: auto;">
<img src="https://i.imgur.com/6bjNsYU.gif" alt="logo" class="responsive" style="width: 30%; height: auto;">
<img src="https://i.imgur.com/6bjNsYU.gif" alt="logo" class="responsive" style="width: 30%; height: auto;">


They are named Robert, Lucie, Annie, James and Stacy.

You'll define one service that needs one hamster and one that needs three.
We'll call them `my_light_service` and `my_heavy_service`.

Let's declare the hamsters in the `/etc/docker/daemon.json`. If this file doesn't exist
on your system, you can create it.

Mine looks like this, note that you don't need the insecure registries part:
```json
{
    "insecure-registries": ["127.0.0.1:5000"],
    "node-generic-resources": [
        "hamster=Robert",
        "hamster=Lucie",
        "hamster=Annie",
        "hamster=James",
        "hamster=Stacy"
    ]
}
```

Restart your Docker daemon with `sudo service docker restart`.

Then create a Docker swarm: `docker swarm init`

The hamster are declared, up and ready to go! 
You can check they're here with `docker node ls` and `docker node inspect`.

### Creating services with the CLI

It's time to create services and hit those hamsters!

First we'll create the services with the CLI and then with the command line.
```
$ docker service create --generic-resource "hamster=1" --name my_light_service ubuntu bash -c "env && sleep infinity"
$ docker service create --generic-resource "hamster=3" --name my_heavy_service ubuntu bash -c "env && sleep infinity"
```

We have one replica for the light and heavy service. They use 4 hamster. Let's try to use moooooooore!

```bash
$ docker service scale -d my_light_service=10 my_heavy_service=10
$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE               PORTS
tt436bxjtdn7        my_heavy_service    replicated          1/10                 ubuntu:latest
ksiq5x0bxch1        my_light_service    replicated          2/10                 ubuntu:latest
```

Remember, we only have 5 hamsters, and 3 are needed for the heavy service and one for the light service.
Hence here 2 * 1 + 1 * 3 = 5 ! This is what we wanted. So how does each container knows which hamster to use?

We asked each container to print the environment variables and sleep for infinity `env && sleep infinity`.
Let's take a look with `docker logs`:

```bash
$ docker ps
CONTAINER ID IMAGE          COMMAND                NAMES
1e8932f5a985 ubuntu:latest  "bash -c 'env && sle…" my_light_service.4.shys2wwxz7jjfjg2g2e0xl1sw
0a5c4ddd303a ubuntu:latest  "bash -c 'env && sle…" my_heavy_service.1.p39satddgf6j1uhspdiohcyzh
e2872006cc97 ubuntu:latest  "bash -c 'env && sle…" my_light_service.1.bbo0fbi5d5e2zdwozgbse8x57

$ docker logs my_light_service.4.shys2wwxz7jjfjg2g2e0xl1sw
DOCKER_RESOURCE_HAMSTER=Stacy
HOSTNAME=1e8932f5a985

$ docker logs my_heavy_service.1.p39satddgf6j1uhspdiohcyzh
DOCKER_RESOURCE_HAMSTER=Lucie,Annie,James
HOSTNAME=0a5c4ddd303a

$ docker logs my_light_service.1.bbo0fbi5d5e2zdwozgbse8x57
DOCKER_RESOURCE_HAMSTER=Robert
HOSTNAME=e2872006cc97
```

So we can see that each container is aware of it's hamster with an environment variable.
The process running in the container can grab it and then use the correct hamster without 
making two containers use the same hamster.

### Using hamsters with Docker stack

Here is a `docker-compose.yml` that will declare the services exactly like we did in the CLI:

```yaml
version: "3.8"

services:
  my_light_service:
    command:
      - bash
      - -c
      - env && sleep infinity
    image: ubuntu
    deploy:
      replicas: 10
      resources:
        reservations:
          generic_resources:
            - discrete_resource_spec:
                kind: 'hamster'
                value: 1

  my_heavy_service:
    command:
      - bash
      - -c
      - env && sleep infinity
    image: ubuntu
    deploy:
      replicas: 10
      resources:
        reservations:
          generic_resources:
            - discrete_resource_spec:
                kind: 'hamster'
                value: 3
```

```bash
$ docker stack deploy -c docker-compose.yml my_stack_using_hamsters
Creating network my_stack_using_hamsters_default
Creating service my_stack_using_hamsters_my_heavy_service
Creating service my_stack_using_hamsters_my_light_service

$ docker service ls
ID              NAME                                       MODE        REPLICAS  IMAGE 
nlhwfnz0d1cx    my_stack_using_hamsters_my_heavy_service   replicated  1/10      ubuntu:latest
c77tv3czzfw2    my_stack_using_hamsters_my_light_service   replicated  2/10      ubuntu:latest
```


### How does that fit with Nvidia GPUs?

Well, if you remember, the Nvidia runtime uses environment variables in the container to know which gpu to use.

By modifying the `/etc/nvidia-container-runtime/config.toml`, 
and setting `swarm-resource = "DOCKER_RESOURCE_GPU"`, it indicates the nvidia-docker runtime 
that it should watch for this environment variable when deciding which gpu to use.
Make the nvidia-docker runtime the default one for this node, replace hamster by gpu and you're good to
go as long as you used UUID as your hamster's names.

A more in depth guide can be found [here](https://gist.github.com/tomlankhorst/33da3c4b9edbde5c83fc1244f010815c).




## Discreet resources

TODO (just put `"node-generic-resources": ["hamster=100"]` in the daemon.json, there are too many hamsters to give them names).

 