"""
SMS Bomber API Module
Loads providers from compiled bytecode (.pyc) or source (.py)
"""

import os

_dir = os.path.dirname(os.path.abspath(__file__))

# Check if compiled version exists
_use_compiled = os.path.exists(os.path.join(_dir, "providers.pyc"))

if _use_compiled:
    # Load from compiled bytecode
    from ._loader import Provider, ProviderRegistry, CallProvider, CallProviderRegistry
else:
    # Load from source (development mode)
    from .providers import Provider, ProviderRegistry
    from .call_providers import CallProvider, CallProviderRegistry

from .client import APIClient
from .call_client import CallBomberClient

__all__ = [
    'Provider',
    'ProviderRegistry',
    'CallProvider', 
    'CallProviderRegistry',
    'APIClient',
    'CallBomberClient',
]
