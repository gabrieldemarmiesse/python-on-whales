import pytest

from docker_cli_wrapper import DockerException, docker
from docker_cli_wrapper.components.image import ImageInspectResult, bulk_reload


def test_image_remove():
    docker.image.pull("busybox:1", quiet=True)
    docker.image.pull("busybox:1.32", quiet=True)
    docker.image.remove(["busybox:1", "busybox:1.32"])


def test_image_save_load(tmp_path):
    tar_file = tmp_path / "dodo.tar"
    docker.image.pull("busybox:1", quiet=True)
    docker.image.save("busybox:1", output=tar_file)
    docker.image.remove("busybox:1")
    docker.image.load(input=tar_file)


def test_save_iterator_bytes():
    docker.image.pull("busybox:1", quiet=True)
    iterator = docker.image.save("busybox:1")

    for i, my_bytes in enumerate(iterator):
        if i == 0:
            assert len(my_bytes) != 0

    assert i != 0


def test_save_iterator_bytes_fails():
    docker.image.pull("busybox:1", quiet=True)
    iterator = docker.image.save("busybox:42")

    with pytest.raises(DockerException) as err:
        for _ in iterator:
            pass
    assert "docker image save busybox:42" in str(err.value)
    assert "Error response from daemon: reference does not exist" in str(err.value)


def test_save_iterator_bytes_and_load():
    image_name = "busybox:1"
    docker.image.pull(image_name, quiet=True)
    iterator = docker.image.save(image_name)

    my_tar_as_bytes = b"".join(iterator)

    docker.image.remove(image_name)

    docker.image.load(my_tar_as_bytes)
    docker.image.remove(image_name)  # TODO: use list instead.


def test_save_iterator_bytes_and_load_from_iterator():
    image_name = "busybox:1"
    docker.image.pull(image_name, quiet=True)
    iterator = docker.image.save(image_name)

    docker.image.load(iterator)
    docker.image.remove(image_name)  # TODO: use list instead.


def test_image_list():
    for image in docker.image.list():
        image.reload()
        assert image.id == image._image_inspect_result.Id


def test_image_list_bulk_reload():
    all_images = docker.image.list()
    bulk_reload(all_images)
    for image in all_images:
        assert image.id == image._image_inspect_result.Id


def test_image_list_tags():
    image_name = "busybox:1"
    docker.image.pull(image_name, quiet=True)
    all_images = docker.image.list()
    for image in all_images:
        if image_name in image.repo_tags:
            return
    else:
        raise ValueError("Tag not found in images.")


def test_pull_not_quiet():
    try:
        docker.image.remove("busybox:1")
    except DockerException:
        pass
    image = docker.image.pull("busybox:1")
    assert "busybox:1" in image.repo_tags


json_inspect_image = """
{
    "Id": "sha256:db646a8f40875981809f754e28a3834e856727b12e7662dad573b6b243e3fba4",
    "RepoTags": [
        "progrium/stress:latest"
    ],
    "RepoDigests": [
        "progrium/stress@sha256:e34d56d60f5caae79333cee395aae93b74791d50e3841986420d23c2ee4697bf"
    ],
    "Parent": "",
    "Comment": "",
    "Created": "2014-07-20T15:21:07.696497913Z",
    "Container": "f13ba377a4cf8258bce8316ab24362500fa0dc28f9e03c80a1e14550efa0f009",
    "ContainerConfig": {
        "Hostname": "0e6756a12879",
        "Domainname": "",
        "User": "",
        "AttachStdin": false,
        "AttachStdout": false,
        "AttachStderr": false,
        "Tty": false,
        "OpenStdin": false,
        "StdinOnce": false,
        "Env": [
            "HOME=/",
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        ],
        "Cmd": [
            "/bin/sh",
            "-c",
            "#(nop) CMD []"
        ],
        "Image": "8d2c32294d3876d8697bc10857397d6d515c1ed6942c8ae03e95e58684ae3a62",
        "Volumes": null,
        "WorkingDir": "",
        "Entrypoint": [
            "/usr/bin/stress",
            "--verbose"
        ],
        "OnBuild": [],
        "Labels": null
    },
    "DockerVersion": "1.1.0",
    "Author": "Jeff Lindsay <progrium@gmail.com>",
    "Config": {
        "Hostname": "0e6756a12879",
        "Domainname": "",
        "User": "",
        "AttachStdin": false,
        "AttachStdout": false,
        "AttachStderr": false,
        "Tty": false,
        "OpenStdin": false,
        "StdinOnce": false,
        "Env": [
            "HOME=/",
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        ],
        "Cmd": [],
        "Image": "8d2c32294d3876d8697bc10857397d6d515c1ed6942c8ae03e95e58684ae3a62",
        "Volumes": null,
        "WorkingDir": "",
        "Entrypoint": [
            "/usr/bin/stress",
            "--verbose"
        ],
        "OnBuild": [],
        "Labels": null
    },
    "Architecture": "amd64",
    "Os": "linux",
    "Size": 281783943,
    "VirtualSize": 281783943,
    "GraphDriver": {
        "Data": {
            "LowerDir": "/var/lib/docker/overlay2/0f34a1116ce5fc3d2814ccd4ff6c5998467bf773b50dc1f3e9de8a3e26536dda/diff:/var/lib/docker/overlay2/ecd27b6e69106899a3fcc22faa764b73f605b857b694bcbea2b1df7da672477e/diff:/var/lib/docker/overlay2/79b527d6e8e3bd3b2a90de547eb8c65d74d10d3d5b4bf2a11b8880742b6dd9e8/diff:/var/lib/docker/overlay2/176ec1f59bf4e783d29fee797c90a0baa9acdb556a5718cde195783803e11e87/diff:/var/lib/docker/overlay2/672f340dc0780643d9e07d17969a0f4ad7ead31669b22a62e369c5b374c02193/diff:/var/lib/docker/overlay2/6d1272fb84716e0c5fc155a0ccfe53ac93ffa6ca5bba4ab78f380167a2b902de/diff:/var/lib/docker/overlay2/bf0acd30d8c5f43f6dce89e3e6201e3b74fccefdd025538c363e57058a8068c7/diff:/var/lib/docker/overlay2/ebaedc0f8f09e96821a6fba4878ade18ff50dabbb4fbe432fc665a06a382383b/diff:/var/lib/docker/overlay2/6d59c976356df2d5062f720e7a0dc0eab32e0c14f3386ab2704471fa91415283/diff",
            "MergedDir": "/var/lib/docker/overlay2/62be51b0b523aa51710f777229bd396b7a5e11df274243d38d8a765f87041fc7/merged",
            "UpperDir": "/var/lib/docker/overlay2/62be51b0b523aa51710f777229bd396b7a5e11df274243d38d8a765f87041fc7/diff",
            "WorkDir": "/var/lib/docker/overlay2/62be51b0b523aa51710f777229bd396b7a5e11df274243d38d8a765f87041fc7/work"
        },
        "Name": "overlay2"
    },
    "RootFS": {
        "Type": "layers",
        "Layers": [
            "sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef",
            "sha256:8200f77c555bbcf7537cb9257f643a07adf179015d8c0789fd8ea42c269e78e7",
            "sha256:5004946741d13ef6fba4d9dbc7e6ffde72f8ead31d569b32ca9593359312aa28",
            "sha256:df60166f50feff0e4f9c52812b6012691489335d697fe73ee1bda664e0f180ca",
            "sha256:eb9586760c19b22518d06d0b876dfd935ed6e1ac56c66dded1e613d74ce197f2",
            "sha256:8744facfa470522aa3e2945cd3359ee2ef5a9d9f27366cbc1d12df17ac472e69",
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "sha256:1e47ff17b890c88095e57289a40b225e95272ea058dd1397436ab9e7d196b820",
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ]
    },
    "Metadata": {
        "LastTagTime": "0001-01-01T00:00:00Z"
    }
}
"""


def test_parse_inspect():
    some_object = ImageInspectResult.parse_raw(json_inspect_image)

    assert some_object.RepoTags == ["progrium/stress:latest"]
