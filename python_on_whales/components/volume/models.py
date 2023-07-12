from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class VolumeInspectResult(DockerCamelModel):
    name: Optional[str]
    driver: Optional[str]
    mountpoint: Optional[Path]
    created_at: Optional[datetime]
    status: Optional[Dict[str, Any]]
    labels: Optional[Dict[str, str]]
    scope: Optional[str]
    options: Optional[Dict[str, str]]
