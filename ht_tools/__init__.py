import json
from pathlib import Path
from importlib.resources import files


# DEFAULT IBKR CONFIGS
HOST = "localhost"
PORT = 7497
CLIENT_ID = 0

def load_config() -> json:
    try:
        _config_path = files('ht_tools').joinpath('config.json')
        with open(_config_path) as file:
            return json.load(file)
    except Exception as e:
        # Fallback config.json if non existing filr in project root
        config_json = {
            "IBKR": {
                "host": HOST,
                "port": PORT,
                "client_id": CLIENT_ID
            }
        }
        return config_json


# Manage version numbers from package installer
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
