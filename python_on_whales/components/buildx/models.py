from __future__ import annotations
from dataclasses import dataclass, field
from typing import List



@dataclass
class BuilderInspectResult:
    name: str
    driver: str
    nodes: List[BuilderNode] = field(default_factory=lambda: [])

    @classmethod
    def from_str(cls, string: str) -> BuilderInspectResult:
        string = string.strip()
        result_dict = {
            "name": "",
            "driver": "",
            "nodes": [],
        }
        nodes_reached = False
        node = BuilderNode()
        for line in string.splitlines():
            if line.startswith("Nodes:"):
                nodes_reached = True
            if not nodes_reached:
                if line.startswith("Name:"):
                    result_dict["name"] = line.split(":")[1].strip()
                if line.startswith("Driver:"):
                    result_dict["driver"] = line.split(":")[1].strip()

            if nodes_reached:
                if line.startswith("Name:"):
                    node.name = line.split(":")[1].strip()
                if line.startswith("Status:"):
                    node.status = line.split(":")[1].strip()
                if line.startswith("Platforms:"):
                    platforms = line.split(":")[1].strip()
                    if platforms:
                        node.platforms = platforms.split(", ")
                    result_dict["nodes"].append(node)
                    node = BuilderNode()
        return cls(**result_dict)

class BuilderNode:
    name: str = ""
    status: str = ""
    platforms: List[str] = []

    def __str__(self):
        return self.name
