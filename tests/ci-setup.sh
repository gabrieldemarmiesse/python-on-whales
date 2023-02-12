set -ex

cat /etc/docker/daemon.json
echo '{"insecure-registries" : [ "localhost:5000" ]}' | sudo tee /etc/docker/daemon.json
sudo service docker restart
sleep 2
docker info
pip install -e .
pip install -r ./tests/test-requirements.txt

mkdir -p ~/.docker/cli-plugins/
wget -q https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-linux-x86_64 -O ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
wget -q https://github.com/docker/buildx/releases/download/v0.10.0/buildx-v0.10.0.linux-amd64 -O ~/.docker/cli-plugins/docker-buildx
chmod +x ~/.docker/cli-plugins/docker-buildx
