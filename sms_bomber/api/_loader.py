"""
Provider Loader - Loads compiled provider modules (.pyc)
This module handles importing bytecode-compiled providers.
"""

import importlib.util
import importlib.machinery
import sys
import os

_dir = os.path.dirname(os.path.abspath(__file__))


def _load_pyc(module_name, pyc_filename):
    """Load a .pyc file as a module."""
    pyc_path = os.path.join(_dir, pyc_filename)
    
    if not os.path.exists(pyc_path):
        return None
    
    try:
        loader = importlib.machinery.SourcelessFileLoader(module_name, pyc_path)
        spec = importlib.util.spec_from_loader(module_name, loader)
        if spec:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            loader.exec_module(module)
            return module
    except Exception as e:
        print(f"Warning: Could not load {pyc_filename}: {e}")
    
    return None


# Load compiled providers
_providers_mod = _load_pyc("_compiled_providers", "providers.pyc")
_call_providers_mod = _load_pyc("_compiled_call_providers", "call_providers.pyc")

# Export classes
if _providers_mod:
    Provider = _providers_mod.Provider
    ProviderRegistry = _providers_mod.ProviderRegistry
else:
    # Fallback - empty registry
    class Provider:
        pass
    class ProviderRegistry:
        def get_all_providers(self):
            return []

if _call_providers_mod:
    CallProvider = _call_providers_mod.CallProvider
    CallProviderRegistry = _call_providers_mod.CallProviderRegistry
else:
    # Fallback - empty registry
    class CallProvider:
        pass
    class CallProviderRegistry:
        def get_all_providers(self):
            return []
