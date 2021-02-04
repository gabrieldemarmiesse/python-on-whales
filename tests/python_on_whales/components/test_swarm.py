from datetime import timedelta

import pytest

from python_on_whales import docker


@pytest.mark.usefixtures("swarm_mode")
def test_swarm_update_retention_limit():
    docker.swarm.update(task_history_limit=4)
    assert (
        docker.system.info().swarm.cluster.spec.orchestration.task_history_retention_limit
        == 4
    )


@pytest.mark.usefixtures("swarm_mode")
def test_swarm_change_certificate_expiry():
    ca = docker.swarm.ca(certificate_expiry=timedelta(days=1), rotate=True)
    info = docker.system.info()
    node_cert_expiry = timedelta(
        microseconds=info.swarm.cluster.spec.ca_config.node_cert_expiry / 1000
    )
    assert node_cert_expiry == timedelta(days=1)
    assert "BEGIN CERTIFICATE" in ca


@pytest.mark.usefixtures("swarm_mode")
def test_swarm_update_auto_lock_managers():
    assert (
        not docker.system.info().swarm.cluster.spec.encryption_config.auto_lock_managers
    )
    docker.swarm.update(autolock=True)
    assert docker.system.info().swarm.cluster.spec.encryption_config.auto_lock_managers


@pytest.mark.usefixtures("swarm_mode")
def test_swarm_unlock_key():
    docker.swarm.update(autolock=True)
    first_key = docker.swarm.unlock_key()
    # make sure is doesn't change
    assert first_key == docker.swarm.unlock_key()

    # make sure it changes:
    assert first_key != docker.swarm.unlock_key(rotate=True)
