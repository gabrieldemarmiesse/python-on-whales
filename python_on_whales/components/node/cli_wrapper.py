from __future__ import annotations

from typing import Dict, List, Optional, Union, overload

import python_on_whales.components.node.docker_object
import python_on_whales.components.task
from python_on_whales.client_config import DockerCLICaller
from python_on_whales.utils import run, to_list


class NodeCLI(DockerCLICaller):
    def demote(
        self,
        x: Union[
            python_on_whales.components.node.docker_object.ValidNode,
            List[python_on_whales.components.node.docker_object.ValidNode],
        ],
    ):
        """Demote one or more nodes from manager in the swarm

        # Arguments
            x: One or a list of nodes.
        """
        full_cmd = self.docker_cmd + ["node", "demote"]
        full_cmd += to_list(x)
        run(full_cmd)

    @overload
    def inspect(self, x: str) -> python_on_whales.components.node.docker_object.Node:
        ...

    @overload
    def inspect(
        self, x: List[str]
    ) -> List[python_on_whales.components.node.docker_object.Node]:
        ...

    def inspect(
        self, x: Union[str, List[str]]
    ) -> Union[
        python_on_whales.components.node.docker_object.Node,
        List[python_on_whales.components.node.docker_object.Node],
    ]:
        """Returns a `python_on_whales.Node` object from a string
        (id or hostname of the node)

        # Arguments
            x: One id or hostname or a list of ids or hostnames

        # Returns
            One or a list of `python_on_whales.Node`
        """
        if isinstance(x, str):
            return python_on_whales.components.node.docker_object.Node(
                self.client_config, x
            )
        else:
            return [
                python_on_whales.components.node.docker_object.Node(
                    self.client_config, reference
                )
                for reference in x
            ]

    def list(self) -> List[python_on_whales.components.node.docker_object.Node]:
        """Returns the list of nodes in this swarm.

        # Returns
            A `List[python_on_whales.Node]`
        """
        full_cmd = self.docker_cmd + ["node", "list", "--quiet"]
        all_ids = run(full_cmd).splitlines()
        return [
            python_on_whales.components.node.docker_object.Node(
                self.client_config, x, is_immutable_id=True
            )
            for x in all_ids
        ]

    def promote(
        self,
        x: Union[
            python_on_whales.components.node.docker_object.ValidNode,
            List[python_on_whales.components.node.docker_object.ValidNode],
        ],
    ):
        """Promote one or more nodes to manager in the swarm

        # Arguments
            x: One or a list of nodes.
        """
        full_cmd = self.docker_cmd + ["node", "promote"]
        full_cmd += to_list(x)
        run(full_cmd)

    def ps(
        self,
        x: Union[
            python_on_whales.components.node.docker_object.ValidNode,
            List[python_on_whales.components.node.docker_object.ValidNode],
        ] = [],
    ) -> List[python_on_whales.components.task.Task]:
        """Returns the list of swarm tasks running on one or more nodes.

        ```python
        from python_on_whales import docker

        tasks = docker.node.ps("my-node-name")
        print(tasks[0].desired_state)
        # running
        ```

        # Arguments
            x: One or more nodes (can be id, name or `python_on_whales.Node` object.).
                If the argument is not provided, it defaults to the current node.

        # Returns
            `List[python_on_whales.Task]`
        """
        full_cmd = (
            self.docker_cmd + ["node", "ps", "--quiet", "--no-trunc"] + to_list(x)
        )
        ids = run(full_cmd).splitlines()
        return [
            python_on_whales.components.task.Task(
                self.client_config, id_, is_immutable_id=True
            )
            for id_ in ids
        ]

    def remove(
        self,
        x: Union[
            python_on_whales.components.node.docker_object.ValidNode,
            List[python_on_whales.components.node.docker_object.ValidNode],
        ],
        force: bool = False,
    ):
        """Remove one or more nodes from the swarm

        # Arguments
            x: One node or a list of nodes. You can use the id or the hostname of a node.
                You can also use a `python_on_whales.Node`.
            force: Force remove a node from the swarm
        """
        full_cmd = self.docker_cmd + ["node", "remove"]
        full_cmd.add_flag("--force", force)
        full_cmd += to_list(x)
        run(full_cmd)

    def update(
        self,
        node: python_on_whales.components.node.docker_object.ValidNode,
        availability: Optional[str] = None,
        labels_add: Dict[str, str] = {},
        rm_labels: List[str] = [],
        role: Optional[str] = None,
    ) -> None:
        """Updates a Swarm node.

        # Arguments
            node: The node to update, you can use a string or a `python_on_whales.Node`
                object.
            availability: Availability of the node ("active"|"pause"|"drain")
            labels_add: Remove a node label if exists
            rm_labels: Labels to remove from the node.
            role: Role of the node ("worker"|"manager")
        """
        full_cmd = self.docker_cmd + ["node", "update"]

        full_cmd.add_simple_arg("--availability", availability)
        for label_name, label_value in labels_add.items():
            full_cmd += ["--label-add", f"{label_name}={label_value}"]

        for label in rm_labels:
            full_cmd += ["--rm-label", label]

        full_cmd.add_simple_arg("--role", role)
        full_cmd.append(node)
        run(full_cmd)
