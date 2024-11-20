#!/usr/bin/env bash

set -ex

THIS_DIR=$(dirname "${BASH_SOURCE[0]}")

"$THIS_DIR"/add-local-docker-registry.sh
"$THIS_DIR"/download-docker-plugins.sh
"$THIS_DIR"/ci-podman-update.sh

docker info
podman info
