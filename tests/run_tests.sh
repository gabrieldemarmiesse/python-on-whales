set -e -x

export DOCKER_CLI_EXPERIMENTAL=enabled

docker buildx bake --load

docker run -v /var/run/docker.sock:/var/run/docker.sock tests-with-binaries-python-on-whales
docker run -v /var/run/docker.sock:/var/run/docker.sock tests-without-any-binary-python-on-whales
