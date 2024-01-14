#!/usr/bin/env bash

set -ex

THIS_DIR=$(dirname "${BASH_SOURCE[0]}")

"$THIS_DIR"/add-local-docker-registry.sh
"$THIS_DIR"/download-docker-plugins.sh
docker info
podman info

pip install -U pip wheel
pip install -e ./
pip install -r tests/test-requirements.txt
