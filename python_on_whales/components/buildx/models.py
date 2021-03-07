from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BuilderInspectResult:
    name: str
    driver: str

    @classmethod
    def from_str(cls, string: str) -> BuilderInspectResult:
        string = string.strip()
        result_dict = {}
        for line in string.splitlines():
            if line.startswith("Name:") and "name" not in result_dict:
                result_dict["name"] = line.split(":")[1].strip()
            if line.startswith("Driver:"):
                result_dict["driver"] = line.split(":")[1].strip()

        return cls(**result_dict)
