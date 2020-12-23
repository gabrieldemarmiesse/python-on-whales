from python_on_whales import docker


def write_code(i: int, attribute_access: str, value) -> str:
    string = f"""In [{i}]: super_print({attribute_access})
type = {type(value)}, value = {value}
"""
    return string


def generate_code_demo_volumes() -> str:
    result = []

    volume = docker.volume.create()

    with volume:
        to_evaluate = [
            "volume.name",
            "volume.driver",
            "volume.mountpoint",
            "volume.created_at",
            "volume.status",
            "volume.labels",
            "volume.scope",
            "volume.options",
        ]

        for i, attribute_access in enumerate(to_evaluate):
            value = eval(attribute_access)
            result.append(write_code(i + 4, attribute_access, value))

    return "\n".join(result)


def generate_code_demo_images() -> str:
    result = []

    image = docker.pull("ubuntu")
    print(f"Generating example for {image.repo_tags}")
    to_evaluate = [
        "image.id",
        "image.repo_tags",
        "image.repo_digests",
        "image.parent",
        "image.comment",
        "image.created",
        "image.container",
        "image.container_config",
        "image.docker_version",
        "image.author",
        "image.config",
        "image.architecture",
        "image.os",
        "image.os_version",
        "image.size",
        "image.virtual_size",
        "image.graph_driver.name",
        "image.graph_driver.data",
        "image.root_fs.type",
        "image.root_fs.layers",
        "image.root_fs.base_layer",
        "image.metadata",
    ]

    for i, attribute_access in enumerate(to_evaluate):
        value = eval(attribute_access)
        result.append(write_code(i + 4, attribute_access, value))

    return "\n".join(result)


def generate_code_demo_containers():
    result = []

    container = docker.run("ubuntu", ["sleep", "infinity"], detach=True)

    with container:
        to_evaluate = [
            "container.id",
            "container.created",
            "container.path",
            "container.args",
            "container.state.status",
            "container.state.running",
            "container.state.paused",
            "container.state.restarting",
            "container.state.oom_killed",
            "container.state.dead",
            "container.state.pid",
            "container.state.exit_code",
            "container.state.error",
            "container.state.started_at",
            "container.state.finished_at",
            "container.state.health",
            "container.image",
            "container.resolv_conf_path",
            "container.hostname_path",
            "container.hosts_path",
            "container.log_path",
            "container.node",
            "container.name",
            "container.restart_count",
            "container.driver",
            "container.platform",
            "container.mount_label",
            "container.process_label",
            "container.app_armor_profile",
            "container.exec_ids",
            "container.host_config.cpu_shares",
            "container.host_config.memory",
            "container.host_config.cgroup_parent",
            "container.host_config.blkio_weight",
            "container.host_config.blkio_weight_device",
            "container.host_config.blkio_device_read_bps",
            "container.host_config.blkio_device_write_bps",
            "container.host_config.blkio_device_read_iops",
            "container.host_config.blkio_device_write_iops",
            "container.host_config.cpu_period",
            "container.host_config.cpu_quota",
            "container.host_config.cpu_realtime_period",
            "container.host_config.cpu_realtime_runtime",
            "container.host_config.cpuset_cpus",
            "container.host_config.cpuset_mems",
            "container.host_config.devices",
            "container.host_config.device_cgroup_rules",
            "container.host_config.device_requests",
            "container.host_config.kernel_memory",
            "container.host_config.kernel_memory_tcp",
            "container.host_config.memory_reservation",
            "container.host_config.memory_swap",
            "container.host_config.memory_swappiness",
            "container.host_config.nano_cpus",
            "container.host_config.oom_kill_disable",
            "container.host_config.init",
            "container.host_config.pids_limit",
            "container.host_config.ulimits",
            "container.host_config.cpu_count",
            "container.host_config.cpu_percent",
            "container.host_config.binds",
            "container.host_config.container_id_file",
            "container.host_config.log_config",
            "container.host_config.network_mode",
            "container.host_config.port_bindings",
            "container.host_config.restart_policy",
            "container.host_config.auto_remove",
            "container.host_config.volume_driver",
            "container.host_config.volumes_from",
            "container.host_config.mounts",
            "container.host_config.capabilities",
            "container.host_config.cap_add",
            "container.host_config.cap_drop",
            "container.host_config.dns",
            "container.host_config.dns_options",
            "container.host_config.dns_search",
            "container.host_config.extra_hosts",
            "container.host_config.group_add",
            "container.host_config.ipc_mode",
            "container.host_config.cgroup",
            "container.host_config.links",
            "container.host_config.oom_score_adj",
            "container.host_config.pid_mode",
            "container.host_config.privileged",
            "container.host_config.publish_all_ports",
            "container.host_config.readonly_rootfs",
            "container.host_config.security_opt",
            "container.host_config.storage_opt",
            "container.host_config.tmpfs",
            "container.host_config.uts_mode",
            "container.host_config.userns_mode",
            "container.host_config.shm_size",
            "container.host_config.sysctls",
            "container.host_config.runtime",
            "container.host_config.console_size",
            "container.host_config.isolation",
            "container.host_config.masked_paths",
            "container.host_config.readonly_paths",
            "container.graph_driver.name",
            "container.graph_driver.data",
            "container.size_rw",
            "container.size_root_fs",
            "container.mounts",
            "container.config",
            "container.network_settings.bridge",
            "container.network_settings.sandbox_id",
            "container.network_settings.hairpin_mode",
            "container.network_settings.link_local_ipv6_address",
            "container.network_settings.link_local_ipv6_prefix_lenght",
            "container.network_settings.ports",
            "container.network_settings.sandbox_key",
            "container.network_settings.secondary_ip_addresses",
            "container.network_settings.secondary_ipv6_addresses",
            "container.network_settings.endpoint_id",
            "container.network_settings.gateway",
            "container.network_settings.global_ipv6_address",
            "container.network_settings.global_ipv6_prefix_lenght",
            "container.network_settings.ip_adress",
            "container.network_settings.ip_prefix_lenght",
            "container.network_settings.ipv6_gateway",
            "container.network_settings.mac_address",
            "container.network_settings.networks",
        ]

        for i, attribute_access in enumerate(to_evaluate):
            value = eval(attribute_access)
            result.append(write_code(i + 4, attribute_access, value))

    return "\n".join(result)


def add_links(text):
    text = text.replace(
        "`python_on_whales.Container`",
        "[`python_on_whales.Container`](/docker_objects/containers/)",
    )

    return text
