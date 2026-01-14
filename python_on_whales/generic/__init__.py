"""Generic types for python-on-whales.

This subpackage exists to provide a stable import surface:

```python
from python_on_whales.generic import ContainerEngineClient, Image, Network
```
"""

from ..components.system.models import SystemInfo
from .generic_client import ContainerEngineClient

__all__ = [
    "ContainerEngineClient",
    "SystemInfo",
]
