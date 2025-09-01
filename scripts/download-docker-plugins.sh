#!/usr/bin/env bash

set -e

mkdir -p ~/.docker/cli-plugins/
wget -q https://github.com/docker/compose/releases/download/v2.35.0/docker-compose-linux-x86_64 -O ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
wget -q https://github.com/docker/buildx/releases/download/v0.13.0/buildx-v0.13.0.linux-amd64 -O ~/.docker/cli-plugins/docker-buildx
chmod +x ~/.docker/cli-plugins/docker-buildx
