set -e -x

docker buildx build  --network=host --load -f tests/Dockerfile --target lint -t test-image-python-on-whales .

docker buildx build --network=host --load -f tests/Dockerfile --target tests_with_binaries -t test-image-python-on-whales .
docker run -v /var/run/docker.sock:/var/run/docker.sock test-image-python-on-whales


docker buildx build --network=host --load -f tests/Dockerfile --target tests_without_any_binary -t test-image-python-on-whales .
docker run -v /var/run/docker.sock:/var/run/docker.sock test-image-python-on-whales
