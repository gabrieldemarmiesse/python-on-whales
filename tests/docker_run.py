from docker_cli_wrapper import DockerClient

docker = DockerClient()


def test_simple_command():
    output = docker.run("hello-world")

    assert "Hello from Docker!" in output
