import json

from datetime import datetime
from pathlib import Path
from importlib.resources import files

def load_config() -> json:
    _config_path = files('ht_tools').joinpath('config.json')
    if not _config_path.is_file():
        # Non blocking warning since logging is not setup yet
        print(f"> WARNING - Config File not found: {_config_path}")    
    
    with open(_config_path) as file:
        return json.load(file)