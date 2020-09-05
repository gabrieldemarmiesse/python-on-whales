set -e -x


DOCKER_CLI_EXPERIMENTAL=enabled docker buildx build -f tests/Dockerfile --target tests_with_cli -t test-image-python-on-whales .
docker run -v /var/run/docker.sock:/var/run/docker.sock test-image-python-on-whales


DOCKER_CLI_EXPERIMENTAL=enabled docker buildx build -f tests/Dockerfile --target tests_without_cli -t test-image-python-on-whales .
docker run -v /var/run/docker.sock:/var/run/docker.sock test-image-python-on-whales


DOCKER_CLI_EXPERIMENTAL=enabled docker buildx build -f tests/Dockerfile --target tests_ubuntu_install_without_buildx -t test-image-python-on-whales .
docker run -v /var/run/docker.sock:/var/run/docker.sock test-image-python-on-whales
