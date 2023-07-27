from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from python_on_whales.utils import DockerCamelModel


class VolumeInspectResult(DockerCamelModel):
    name: Optional[str] = None
    driver: Optional[str] = None
    mountpoint: Optional[Path] = None
    created_at: Optional[datetime] = None
    status: Optional[Dict[str, Any]] = None
    labels: Optional[Dict[str, str]] = None
    scope: Optional[str] = None
    options: Optional[Dict[str, str]] = None
