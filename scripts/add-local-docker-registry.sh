#!/usr/bin/env bash

set -e

cat /etc/docker/daemon.json || true
echo '{"insecure-registries" : [ "localhost:5000" ]}' | sudo tee /etc/docker/daemon.json
sudo service docker restart
sleep 2
