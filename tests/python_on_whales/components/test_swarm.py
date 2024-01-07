from datetime import timedelta

import pytest

from python_on_whales import DockerClient
from python_on_whales.exceptions import NotASwarmManager


@pytest.mark.usefixtures("swarm_mode")
def test_swarm_update_retention_limit(ctr_client: DockerClient):
    ctr_client.swarm.update(task_history_limit=4)
    assert (
        ctr_client.system.info().swarm.cluster.spec.orchestration.task_history_retention_limit
        == 4
    )


@pytest.mark.usefixtures("swarm_mode")
def test_swarm_change_certificate_expiry(ctr_client: DockerClient):
    ca = ctr_client.swarm.ca(certificate_expiry=timedelta(days=1), rotate=True)
    info = ctr_client.system.info()
    node_cert_expiry = timedelta(
        microseconds=info.swarm.cluster.spec.ca_config.node_cert_expiry / 1000
    )
    assert node_cert_expiry == timedelta(days=1)
    assert "BEGIN CERTIFICATE" in ca


@pytest.mark.usefixtures("swarm_mode")
def test_swarm_update_auto_lock_managers(ctr_client: DockerClient):
    assert (
        not ctr_client.system.info().swarm.cluster.spec.encryption_config.auto_lock_managers
    )
    ctr_client.swarm.update(autolock=True)
    assert (
        ctr_client.system.info().swarm.cluster.spec.encryption_config.auto_lock_managers
    )


@pytest.mark.usefixtures("swarm_mode")
def test_swarm_unlock_key(ctr_client: DockerClient):
    ctr_client.swarm.update(autolock=True)
    first_key = ctr_client.swarm.unlock_key()
    # make sure is doesn't change
    assert first_key == ctr_client.swarm.unlock_key()

    # make sure it changes:
    assert first_key != ctr_client.swarm.unlock_key(rotate=True)


def test_swarm_join_token_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.swarm.join_token("manager")

    assert "not a swarm manager" in str(e.value).lower()


def test_update_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.swarm.update(autolock=True)

    assert "not a swarm manager" in str(e.value).lower()


def test_unlock_key_not_swarm_manager(ctr_client: DockerClient):
    with pytest.raises(NotASwarmManager) as e:
        ctr_client.swarm.unlock_key()

    assert "not a swarm manager" in str(e.value).lower()
