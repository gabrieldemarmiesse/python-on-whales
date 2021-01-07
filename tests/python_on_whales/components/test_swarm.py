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
def test_swarm_update_auto_lock_managers():
    assert (
        not docker.system.info().swarm.cluster.spec.encryption_config.auto_lock_managers
    )
    docker.swarm.update(autolock=True)
    assert docker.system.info().swarm.cluster.spec.encryption_config.auto_lock_managers
