import json
from importlib.resources import files


def load_config() -> json:
    _config_file = files('app').joinpath('config.json')
    if not _config_file.is_file():
        # Non blocking warning since logging is not setup yet
        print(f"> WARNING - Config File not found: {_config_file}")  
    with open(_config_file) as file:
        return json.load(file)