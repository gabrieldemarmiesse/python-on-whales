from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class BuilderInspectResult:
    name: str
    driver: str
    status: str
    platforms: List[str] = field(default_factory=lambda: [])

    @classmethod
    def from_str(cls, string: str) -> BuilderInspectResult:

        string = string.strip()
        result_dict = {}
        for line in string.splitlines():
            if line.startswith("Name:") and "name" not in result_dict:
                result_dict["name"] = line.split(":")[1].strip()
            if line.startswith("Driver:"):
                result_dict["driver"] = line.split(":")[1].strip()
            if line.startswith("Status:"):
                result_dict["status"] = line.split(":")[1].strip()
            if line.startswith("Platforms:"):
                platforms = line.split(":")[1].strip()
                if platforms:
                    result_dict["platforms"] = platforms.split(", ")

        return cls(**result_dict)
