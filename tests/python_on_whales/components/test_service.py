import pytest

from python_on_whales import docker
from python_on_whales.components.service import ServiceInspectResult
from python_on_whales.utils import PROJECT_ROOT


@pytest.fixture
def with_test_stack():
    docker.swarm.init()
    docker.stack.deploy(
        "some_stack",
        [PROJECT_ROOT / "tests/python_on_whales/components/test-stack-file.yml"],
    )
    yield
    docker.stack.remove("some_stack")
    docker.swarm.leave(force=True)


@pytest.mark.usefixtures("with_test_stack")
def test_services_inspect():
    all_services = docker.service.list()
    assert len(all_services) == 4


def test_service_inspect_result_1():
    json_inspect = """
{
    "ID": "m3m209zl7pxn513ufboctb3q2",
    "Version": {
        "Index": 102
    },
    "CreatedAt": "2020-11-14T15:12:39.4142383Z",
    "UpdatedAt": "2020-11-14T15:12:39.4169672Z",
    "Spec": {
        "Name": "my_stack_influxdb",
        "Labels": {
            "com.docker.stack.image": "influxdb:1.7",
            "com.docker.stack.namespace": "my_stack"
        },
        "TaskTemplate": {
            "ContainerSpec": {
                "Image": "influxdb:1.7@sha256:481709b32cca5001a6d03022b3a11e152fd4faa3038e5c0b92bb6de59dbbd868",
                "Labels": {
                    "com.docker.stack.namespace": "my_stack"
                },
                "Privileges": {
                    "CredentialSpec": null,
                    "SELinuxContext": null
                },
                "Mounts": [
                    {
                        "Type": "volume",
                        "Source": "my_stack_influx-data",
                        "Target": "/var/lib/influxdb",
                        "VolumeOptions": {
                            "Labels": {
                                "com.docker.stack.namespace": "my_stack"
                            },
                            "DriverConfig": {
                                "Name": "local"
                            }
                        }
                    }
                ],
                "StopGracePeriod": 10000000000,
                "DNSConfig": {},
                "Isolation": "default"
            },
            "Resources": {
                "Limits": {
                    "NanoCPUs": 600000000,
                    "MemoryBytes": 536870912
                },
                "Reservations": {
                    "NanoCPUs": 300000000,
                    "MemoryBytes": 134217728
                }
            },
            "RestartPolicy": {
                "Condition": "any",
                "Delay": 5000000000,
                "MaxAttempts": 0
            },
            "Placement": {
                "Platforms": [
                    {
                        "Architecture": "amd64",
                        "OS": "linux"
                    },
                    {
                        "OS": "linux"
                    },
                    {
                        "Architecture": "arm64",
                        "OS": "linux"
                    }
                ]
            },
            "Networks": [
                {
                    "Target": "cs2i9dj34n2t3d3axzbfibhbg",
                    "Aliases": [
                        "influxdb"
                    ]
                }
            ],
            "ForceUpdate": 0,
            "Runtime": "container"
        },
        "Mode": {
            "Replicated": {
                "Replicas": 1
            }
        },
        "UpdateConfig": {
            "Parallelism": 1,
            "FailureAction": "pause",
            "Monitor": 5000000000,
            "MaxFailureRatio": 0,
            "Order": "stop-first"
        },
        "RollbackConfig": {
            "Parallelism": 1,
            "FailureAction": "pause",
            "Monitor": 5000000000,
            "MaxFailureRatio": 0,
            "Order": "stop-first"
        },
        "EndpointSpec": {
            "Mode": "vip"
        }
    },
    "Endpoint": {
        "Spec": {
            "Mode": "vip"
        },
        "VirtualIPs": [
            {
                "NetworkID": "cs2i9dj34n2t3d3axzbfibhbg",
                "Addr": "10.0.3.2/24"
            }
        ]
    }
}
    """

    service_inspect_result = ServiceInspectResult.parse_raw(json_inspect)
    assert service_inspect_result.ID == "m3m209zl7pxn513ufboctb3q2"
    assert (
        service_inspect_result.spec.labels["com.docker.stack.image"] == "influxdb:1.7"
    )


def test_service_inspect_result_2():
    json_inspect = """
{
    "ID": "r7iyibbjflmmgsgw7wug7gamm",
    "Version": {
        "Index": 108
    },
    "CreatedAt": "2020-11-14T15:12:41.0319543Z",
    "UpdatedAt": "2020-11-14T15:12:41.0357977Z",
    "Spec": {
        "Name": "my_stack_agent",
        "Labels": {
            "com.docker.stack.image": "swarmpit/agent:latest",
            "com.docker.stack.namespace": "my_stack",
            "swarmpit.agent": "true"
        },
        "TaskTemplate": {
            "ContainerSpec": {
                "Image": "swarmpit/agent:latest@sha256:f92ba65f7923794d43ebffc88fbd49bfe8cde8db48ca6888ece5747b9ab1375c",
                "Labels": {
                    "com.docker.stack.namespace": "my_stack"
                },
                "Env": [
                    "DOCKER_API_VERSION=1.35"
                ],
                "Privileges": {
                    "CredentialSpec": null,
                    "SELinuxContext": null
                },
                "Mounts": [
                    {
                        "Type": "bind",
                        "Source": "/var/run/docker.sock",
                        "Target": "/var/run/docker.sock",
                        "ReadOnly": true
                    }
                ],
                "StopGracePeriod": 10000000000,
                "DNSConfig": {},
                "Isolation": "default"
            },
            "Resources": {
                "Limits": {
                    "NanoCPUs": 100000000,
                    "MemoryBytes": 67108864
                },
                "Reservations": {
                    "NanoCPUs": 50000000,
                    "MemoryBytes": 33554432
                }
            },
            "RestartPolicy": {
                "Condition": "any",
                "Delay": 5000000000,
                "MaxAttempts": 0
            },
            "Placement": {
                "Platforms": [
                    {
                        "Architecture": "amd64",
                        "OS": "linux"
                    },
                    {
                        "Architecture": "arm64",
                        "OS": "linux"
                    },
                    {
                        "OS": "linux"
                    },
                    {
                        "OS": "linux"
                    }
                ]
            },
            "Networks": [
                {
                    "Target": "cs2i9dj34n2t3d3axzbfibhbg",
                    "Aliases": [
                        "agent"
                    ]
                }
            ],
            "ForceUpdate": 0,
            "Runtime": "container"
        },
        "Mode": {
            "Global": {}
        },
        "UpdateConfig": {
            "Parallelism": 1,
            "FailureAction": "pause",
            "Monitor": 5000000000,
            "MaxFailureRatio": 0,
            "Order": "stop-first"
        },
        "RollbackConfig": {
            "Parallelism": 1,
            "FailureAction": "pause",
            "Monitor": 5000000000,
            "MaxFailureRatio": 0,
            "Order": "stop-first"
        },
        "EndpointSpec": {
            "Mode": "vip"
        }
    },
    "Endpoint": {
        "Spec": {
            "Mode": "vip"
        },
        "VirtualIPs": [
            {
                "NetworkID": "cs2i9dj34n2t3d3axzbfibhbg",
                "Addr": "10.0.3.5/24"
            }
        ]
    }
}
    """
    service_inspect_result = ServiceInspectResult.parse_raw(json_inspect)


def test_service_inspect_result_3():
    json_inspect = """
{
    "ID": "v1z59cs9evr57w36xv3a4r4ny",
    "Version": {
        "Index": 115
    },
    "CreatedAt": "2020-11-14T15:12:42.9316045Z",
    "UpdatedAt": "2020-11-14T15:12:42.9344438Z",
    "Spec": {
        "Name": "my_stack_app",
        "Labels": {
            "com.docker.stack.image": "swarmpit/swarmpit:latest",
            "com.docker.stack.namespace": "my_stack"
        },
        "TaskTemplate": {
            "ContainerSpec": {
                "Image": "swarmpit/swarmpit:latest@sha256:20fddbdb7b352a5ac06f6d88bcc0ca4f67a45f1a14b18d557f01052a97a27147",
                "Labels": {
                    "com.docker.stack.namespace": "my_stack"
                },
                "Env": [
                    "SWARMPIT_DB=http://db:5984",
                    "SWARMPIT_INFLUXDB=http://influxdb:8086"
                ],
                "Privileges": {
                    "CredentialSpec": null,
                    "SELinuxContext": null
                },
                "Mounts": [
                    {
                        "Type": "bind",
                        "Source": "/var/run/docker.sock",
                        "Target": "/var/run/docker.sock",
                        "ReadOnly": true
                    }
                ],
                "StopGracePeriod": 10000000000,
                "Healthcheck": {
                    "Test": [
                        "CMD",
                        "curl",
                        "-f",
                        "http://localhost:8080"
                    ],
                    "Interval": 60000000000,
                    "Timeout": 10000000000,
                    "Retries": 3
                },
                "DNSConfig": {},
                "Isolation": "default"
            },
            "Resources": {
                "Limits": {
                    "NanoCPUs": 500000000,
                    "MemoryBytes": 1073741824
                },
                "Reservations": {
                    "NanoCPUs": 250000000,
                    "MemoryBytes": 536870912
                }
            },
            "RestartPolicy": {
                "Condition": "any",
                "Delay": 5000000000,
                "MaxAttempts": 0
            },
            "Placement": {
                "Constraints": [
                    "node.role == manager"
                ],
                "Platforms": [
                    {
                        "Architecture": "amd64",
                        "OS": "linux"
                    },
                    {
                        "Architecture": "arm64",
                        "OS": "linux"
                    },
                    {
                        "OS": "linux"
                    },
                    {
                        "OS": "linux"
                    }
                ]
            },
            "Networks": [
                {
                    "Target": "cs2i9dj34n2t3d3axzbfibhbg",
                    "Aliases": [
                        "app"
                    ]
                }
            ],
            "ForceUpdate": 0,
            "Runtime": "container"
        },
        "Mode": {
            "Replicated": {
                "Replicas": 1
            }
        },
        "UpdateConfig": {
            "Parallelism": 1,
            "FailureAction": "pause",
            "Monitor": 5000000000,
            "MaxFailureRatio": 0,
            "Order": "stop-first"
        },
        "RollbackConfig": {
            "Parallelism": 1,
            "FailureAction": "pause",
            "Monitor": 5000000000,
            "MaxFailureRatio": 0,
            "Order": "stop-first"
        },
        "EndpointSpec": {
            "Mode": "vip",
            "Ports": [
                {
                    "Protocol": "tcp",
                    "TargetPort": 8080,
                    "PublishedPort": 888,
                    "PublishMode": "ingress"
                }
            ]
        }
    },
    "Endpoint": {
        "Spec": {
            "Mode": "vip",
            "Ports": [
                {
                    "Protocol": "tcp",
                    "TargetPort": 8080,
                    "PublishedPort": 888,
                    "PublishMode": "ingress"
                }
            ]
        },
        "Ports": [
            {
                "Protocol": "tcp",
                "TargetPort": 8080,
                "PublishedPort": 888,
                "PublishMode": "ingress"
            }
        ],
        "VirtualIPs": [
            {
                "NetworkID": "ejkqulgep23uu3a5bmgudnibe",
                "Addr": "10.0.0.7/24"
            },
            {
                "NetworkID": "cs2i9dj34n2t3d3axzbfibhbg",
                "Addr": "10.0.3.7/24"
            }
        ]
    }
}   
    """
    service_inspect_result = ServiceInspectResult.parse_raw(json_inspect)


def test_service_inspect_result_4():
    json_inspect = """
{
    "ID": "ttkkm29xchs0gi83n1g0m7ov4",
    "Version": {
        "Index": 122
    },
    "CreatedAt": "2020-11-14T15:12:44.7495433Z",
    "UpdatedAt": "2020-11-14T15:12:44.7547664Z",
    "Spec": {
        "Name": "my_stack_db",
        "Labels": {
            "com.docker.stack.image": "couchdb:2.3.0",
            "com.docker.stack.namespace": "my_stack"
        },
        "TaskTemplate": {
            "ContainerSpec": {
                "Image": "couchdb:2.3.0@sha256:ee75c9a737e7c48af0170142689959f2d70f93700162fef40818c799dfeecb8e",
                "Labels": {
                    "com.docker.stack.namespace": "my_stack"
                },
                "Privileges": {
                    "CredentialSpec": null,
                    "SELinuxContext": null
                },
                "Mounts": [
                    {
                        "Type": "volume",
                        "Source": "my_stack_db-data",
                        "Target": "/opt/couchdb/data",
                        "VolumeOptions": {
                            "Labels": {
                                "com.docker.stack.namespace": "my_stack"
                            },
                            "DriverConfig": {
                                "Name": "local"
                            }
                        }
                    }
                ],
                "StopGracePeriod": 10000000000,
                "DNSConfig": {},
                "Isolation": "default"
            },
            "Resources": {
                "Limits": {
                    "NanoCPUs": 300000000,
                    "MemoryBytes": 268435456
                },
                "Reservations": {
                    "NanoCPUs": 150000000,
                    "MemoryBytes": 134217728
                }
            },
            "RestartPolicy": {
                "Condition": "any",
                "Delay": 5000000000,
                "MaxAttempts": 0
            },
            "Placement": {
                "Platforms": [
                    {
                        "Architecture": "amd64",
                        "OS": "linux"
                    }
                ]
            },
            "Networks": [
                {
                    "Target": "cs2i9dj34n2t3d3axzbfibhbg",
                    "Aliases": [
                        "db"
                    ]
                }
            ],
            "ForceUpdate": 0,
            "Runtime": "container"
        },
        "Mode": {
            "Replicated": {
                "Replicas": 1
            }
        },
        "UpdateConfig": {
            "Parallelism": 1,
            "FailureAction": "pause",
            "Monitor": 5000000000,
            "MaxFailureRatio": 0,
            "Order": "stop-first"
        },
        "RollbackConfig": {
            "Parallelism": 1,
            "FailureAction": "pause",
            "Monitor": 5000000000,
            "MaxFailureRatio": 0,
            "Order": "stop-first"
        },
        "EndpointSpec": {
            "Mode": "vip"
        }
    },
    "Endpoint": {
        "Spec": {
            "Mode": "vip"
        },
        "VirtualIPs": [
            {
                "NetworkID": "cs2i9dj34n2t3d3axzbfibhbg",
                "Addr": "10.0.3.9/24"
            }
        ]
    }
}
    """
    service_inspect_result = ServiceInspectResult.parse_raw(json_inspect)
