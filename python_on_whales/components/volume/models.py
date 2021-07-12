from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class VolumeInspectResult(DockerCamelModel):
    name: str
    driver: str
    mountpoint: Path
    created_at: datetime
    status: Dict[str, Any]
    labels: Dict[str, str]
    scope: str
    options: Dict[str, str]
