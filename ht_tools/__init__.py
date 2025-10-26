"""HT Tools - IBKR Integration Tools."""
import json
import tomllib
from pathlib import Path

try:
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("ht-tools")
except PackageNotFoundError:
    __version__ = None
    raise RuntimeError("ht_tools package is not installed properly. Check TOML file and use 'pip install -e .'")

def version():
    """Display ht-tools version information."""
    print(f"ht-tools version: {__version__}")

__all__ = ["__version__"]

