# Containers

Don't use the constructor directly. Instead use 
```python
from python_on_whales import docker

my_container = docker.container.inspect("my-container-name")

# for example:
if my_container.state.running:
    my_container.kill()

```
For type hints, use this

```python
from python_on_whales import Container

def print_dodo(container: Container):
    print(container.execute(["echo", "dodo"]))
```

## Attributes

It attributes are the same that you get with the command line:
`docker container inspect ...`

If you want to know the exact structure, you can go to the 
[`docker container inspect` reference page](https://docs.docker.com/engine/api/v1.40/#operation/ContainerInspect)
and click on "200 no error".
An example is worth many lines of descriptions.


```
In [1]: from python_on_whales import docker

In [2]: container = docker.run("ubuntu", ["sleep", "infinity"], detach=True)

In [4]: def super_print(obj):
   ...:     print(f"type={type(obj)}, value={obj}")
   ...:

In [4]: super_print(container.id)
type = <class 'str'>, value = 8de91846ebff133a0e9f781cf832054319fc5530afbdd47b0092bbaed7bd8c9e

In [5]: super_print(container.created)
type = <class 'datetime.datetime'>, value = 2020-12-22 03:53:39.647335+00:00

In [6]: super_print(container.path)
type = <class 'str'>, value = sleep

In [7]: super_print(container.args)
type = <class 'list'>, value = ['infinity']

In [8]: super_print(container.state.status)
type = <class 'str'>, value = running

In [9]: super_print(container.state.running)
type = <class 'bool'>, value = True

In [10]: super_print(container.state.paused)
type = <class 'bool'>, value = False

In [11]: super_print(container.state.restarting)
type = <class 'bool'>, value = False

In [12]: super_print(container.state.oom_killed)
type = <class 'bool'>, value = False

In [13]: super_print(container.state.dead)
type = <class 'bool'>, value = False

In [14]: super_print(container.state.pid)
type = <class 'int'>, value = 11768

In [15]: super_print(container.state.exit_code)
type = <class 'int'>, value = 0

In [16]: super_print(container.state.error)
type = <class 'str'>, value = 

In [17]: super_print(container.state.started_at)
type = <class 'datetime.datetime'>, value = 2020-12-22 03:53:40.379205+00:00

In [18]: super_print(container.state.finished_at)
type = <class 'datetime.datetime'>, value = 0001-01-01 00:00:00+00:00

In [19]: super_print(container.state.health)
type = <class 'NoneType'>, value = None

In [20]: super_print(container.image)
type = <class 'str'>, value = sha256:f643c72bc25212974c16f3348b3a898b1ec1eb13ec1539e10a103e6e217eb2f1

In [21]: super_print(container.resolv_conf_path)
type = <class 'str'>, value = /var/lib/docker/containers/8de91846ebff133a0e9f781cf832054319fc5530afbdd47b0092bbaed7bd8c9e/resolv.conf

In [22]: super_print(container.hostname_path)
type = <class 'pathlib.PosixPath'>, value = /var/lib/docker/containers/8de91846ebff133a0e9f781cf832054319fc5530afbdd47b0092bbaed7bd8c9e/hostname

In [23]: super_print(container.hosts_path)
type = <class 'pathlib.PosixPath'>, value = /var/lib/docker/containers/8de91846ebff133a0e9f781cf832054319fc5530afbdd47b0092bbaed7bd8c9e/hosts

In [24]: super_print(container.log_path)
type = <class 'pathlib.PosixPath'>, value = /var/lib/docker/containers/8de91846ebff133a0e9f781cf832054319fc5530afbdd47b0092bbaed7bd8c9e/8de91846ebff133a0e9f781cf832054319fc5530afbdd47b0092bbaed7bd8c9e-json.log

In [25]: super_print(container.node)
type = <class 'NoneType'>, value = None

In [26]: super_print(container.name)
type = <class 'str'>, value = musing_snyder

In [27]: super_print(container.restart_count)
type = <class 'int'>, value = 0

In [28]: super_print(container.driver)
type = <class 'str'>, value = overlay2

In [29]: super_print(container.platform)
type = <class 'str'>, value = linux

In [30]: super_print(container.mount_label)
type = <class 'str'>, value = 

In [31]: super_print(container.process_label)
type = <class 'str'>, value = 

In [32]: super_print(container.app_armor_profile)
type = <class 'str'>, value = 

In [33]: super_print(container.exec_ids)
type = <class 'NoneType'>, value = None

In [34]: super_print(container.host_config)
type = <class 'python_on_whales.components.container.ContainerHostConfig'>, value = cpu_shares=0 memory=0 cgroup_parent=PosixPath('.') blkio_weight=0 blkio_weight_device=[] blkio_device_read_bps=None blkio_device_write_bps=None blkio_device_read_iops=None blkio_device_write_iops=None cpu_period=0 cpu_quota=0 cpu_realtime_period=0 cpu_realtime_runtime=0 cpuset_cpus='' cpuset_mems='' devices=[] device_cgroup_rules=None device_requests=None kernel_memory=0 kernel_memory_tcp=0 memory_reservation=0 memory_swap=0 memory_swappiness=None nano_cpus=0 oom_kill_disable=False init=None pids_limit=None ulimits=None cpu_count=0 cpu_percent=0 binds=None container_id_file=PosixPath('.') log_config=ContainerLogConfig(type='json-file', config={}) network_mode='default' port_bindings={} restart_policy=ContainerRestartPolicy(name='no', maximum_retry_count=0) auto_remove=False volume_driver='' volumes_from=None mounts=None capabilities=None cap_add=None cap_drop=None dns=[] dns_options=[] dns_search=[] extra_hosts=None group_add=None ipc_mode='private' cgroup='' links=None oom_score_adj=0 pid_mode='' privileged=False publish_all_ports=False readonly_rootfs=False security_opt=None storage_opt=None tmpfs=None uts_mode='' userns_mode='' shm_size=67108864 sysctls=None runtime='runc' console_size=(0, 0) isolation='' masked_paths=[PosixPath('/proc/asound'), PosixPath('/proc/acpi'), PosixPath('/proc/kcore'), PosixPath('/proc/keys'), PosixPath('/proc/latency_stats'), PosixPath('/proc/timer_list'), PosixPath('/proc/timer_stats'), PosixPath('/proc/sched_debug'), PosixPath('/proc/scsi'), PosixPath('/sys/firmware')] readonly_paths=[PosixPath('/proc/bus'), PosixPath('/proc/fs'), PosixPath('/proc/irq'), PosixPath('/proc/sys'), PosixPath('/proc/sysrq-trigger')]

In [35]: super_print(container.graph_driver.name)
type = <class 'str'>, value = overlay2

In [36]: super_print(container.graph_driver.data)
type = <class 'dict'>, value = {'LowerDir': '/var/lib/docker/overlay2/a54955d10fd9cd20f52a3685350a6bec862acfe0e40e25f7433e3f8b80951a98-init/diff:/var/lib/docker/overlay2/559f32baec3b986c62354f959b143b6bbcae64d07af7c2be75bcc1e5780643a0/diff:/var/lib/docker/overlay2/9cb13ec06b26811bb6ad55246f1e5c39d48f8cc5f31ab800272604cfb4ffc453/diff:/var/lib/docker/overlay2/b96f59d6f7a2869dc030b79bbf4883884ba1f2dc79d00c454322cffc62f92f48/diff', 'MergedDir': '/var/lib/docker/overlay2/a54955d10fd9cd20f52a3685350a6bec862acfe0e40e25f7433e3f8b80951a98/merged', 'UpperDir': '/var/lib/docker/overlay2/a54955d10fd9cd20f52a3685350a6bec862acfe0e40e25f7433e3f8b80951a98/diff', 'WorkDir': '/var/lib/docker/overlay2/a54955d10fd9cd20f52a3685350a6bec862acfe0e40e25f7433e3f8b80951a98/work'}

In [37]: super_print(container.size_rw)
type = <class 'NoneType'>, value = None

In [38]: super_print(container.size_root_fs)
type = <class 'NoneType'>, value = None

In [39]: super_print(container.mounts)
type = <class 'list'>, value = []

In [40]: super_print(container.config)
type = <class 'python_on_whales.components.container.ContainerConfig'>, value = hostname='8de91846ebff' domainname='' user='' attach_stdin=False attach_stdout=False attach_stderr=False exposed_ports=None tty=False open_stdin=False stdin_once=False env=['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'] cmd=['sleep', 'infinity'] healthcheck=None args_escaped=None image='ubuntu' volumes=None working_dir=PosixPath('.') entrypoint=None network_disabled=None mac_address=None on_build=None labels={} stop_signal=None stop_timeout=None shell=None

In [41]: super_print(container.network_settings.bridge)
type = <class 'str'>, value = 

In [42]: super_print(container.network_settings.sandbox_id)
type = <class 'str'>, value = f4eace1d029c79014e6f9f0ad68d0748589bd5e8fe8ac22e71f540dd3aa43ee2

In [43]: super_print(container.network_settings.hairpin_mode)
type = <class 'bool'>, value = False

In [44]: super_print(container.network_settings.link_local_ipv6_address)
type = <class 'str'>, value = 

In [45]: super_print(container.network_settings.link_local_ipv6_prefix_lenght)
type = <class 'int'>, value = 0

In [46]: super_print(container.network_settings.ports)
type = <class 'dict'>, value = {}

In [47]: super_print(container.network_settings.sandbox_key)
type = <class 'pathlib.PosixPath'>, value = /var/run/docker/netns/f4eace1d029c

In [48]: super_print(container.network_settings.secondary_ip_addresses)
type = <class 'NoneType'>, value = None

In [49]: super_print(container.network_settings.secondary_ipv6_addresses)
type = <class 'NoneType'>, value = None

In [50]: super_print(container.network_settings.endpoint_id)
type = <class 'str'>, value = b2bc3cfd5f21f1a3aca4bdfdee07a6dc7dad57bd85e8e8c8491ce8ae7ee94cce

In [51]: super_print(container.network_settings.gateway)
type = <class 'str'>, value = 172.17.0.1

In [52]: super_print(container.network_settings.global_ipv6_address)
type = <class 'str'>, value = 

In [53]: super_print(container.network_settings.global_ipv6_prefix_lenght)
type = <class 'int'>, value = 0

In [54]: super_print(container.network_settings.ip_adress)
type = <class 'str'>, value = 172.17.0.3

In [55]: super_print(container.network_settings.ip_prefix_lenght)
type = <class 'int'>, value = 16

In [56]: super_print(container.network_settings.ipv6_gateway)
type = <class 'str'>, value = 

In [57]: super_print(container.network_settings.mac_address)
type = <class 'str'>, value = 02:42:ac:11:00:03

In [58]: super_print(container.network_settings.networks)
type = <class 'dict'>, value = {'bridge': NetworkInspectResult(ipam_config=None, links=None, aliases=None, network_id='a362a2c196192a2360d65c8599e25bc48e95365ea2548febe7a2e420f7169a00', endpoint_id='b2bc3cfd5f21f1a3aca4bdfdee07a6dc7dad57bd85e8e8c8491ce8ae7ee94cce', gateway='172.17.0.1', ip_address='172.17.0.3', ip_prefix_lenght=16, ipv6_gateway='', global_ipv6_address='', global_ipv6_prefix_lenght=0, mac_address='02:42:ac:11:00:03', driver_options=None)}

```

## Methods

{{autogenerated}}
