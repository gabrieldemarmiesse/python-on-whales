set -e -x


DOCKER_CLI_EXPERIMENTAL=enabled docker buildx build -f tests/Dockerfile -t test-image-docker-cli-wrapper .
docker run -v /var/run/docker.sock:/var/run/docker.sock test-image-docker-cli-wrapper
