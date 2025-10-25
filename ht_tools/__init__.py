"""HT Tools - IBKR Integration Tools."""
import tomllib
from pathlib import Path

# Read version from pyproject.toml
_project_root = Path(__file__).parent.parent
_pyproject_path = _project_root / "pyproject.toml"

try:
    with open(_pyproject_path, "rb") as _f:
        _pyproject_data = tomllib.load(_f)
    __version__ = _pyproject_data["project"]["version"]
except (FileNotFoundError, KeyError):
    __version__ = "unknown"

__all__ = ["__version__"]