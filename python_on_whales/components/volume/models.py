from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from python_on_whales.utils import DockerCamelModel


class VolumeInspectResult(DockerCamelModel):
    name: str
    driver: str
    mountpoint: Path
    created_at: datetime
    status: Optional[Dict[str, Any]]
    labels: Optional[Dict[str, str]]
    scope: str
    options: Optional[Dict[str, str]]
