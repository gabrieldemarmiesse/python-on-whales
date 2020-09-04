set -e -x


DOCKER_CLI_EXPERIMENTAL=enabled docker buildx build -f tests/Dockerfile -t test-image-python-on-whales .
docker run -v /var/run/docker.sock:/var/run/docker.sock test-image-python-on-whales
