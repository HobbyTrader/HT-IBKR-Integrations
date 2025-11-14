import json

from importlib.resources import files


_config_path = files('app').joinpath('config.json')

def load_config_logging() -> json:
    try:
        with open(_config_path) as file:
            return json.load(file).get("logging", {
            "logpath": "LOG",
            "logname": "HT_TOOLS.log",
            "loglevel": "DEBUG",
            "consolelevel": "WARNING",
            "backupcount": 10
        })
    except Exception as e:
        # Fallback config.json if non existing filr in project root
        config_json = {
            "logpath": "LOG",
            "logname": "HT_TOOLS.log",
            "loglevel": "DEBUG",
            "consolelevel": "WARNING",
            "backupcount": 10
        }
        return config_json

def load_config_db() -> json:
    try:
        with open(_config_path) as file:
            return json.load(file).get("database", {
            "filename": "app/htibkr.db",
            "tabledefinitions": "app/dto/table_definitions.sql"
        })
    except Exception as e:
        # Fallback config.json if non existing filr in project root
        config_json = {
            "filename": "app/htibkr.db",
            "tabledefinitions": "app/core/sql/table_definitions.sql"
        }
        return config_json
    
def load_config_ibapi() -> json:
    try:
        with open(_config_path) as file:
            return json.load(file).get("IBKR", {
            "HOST": "localhost",
            "PORT": 7497,
            "CLIENTID": "0"
        })
    except Exception as e:
        # Fallback config.json if non existing filr in project root
        config_json = {
            "HOST": "localhost",
            "PORT": 7497,
            "CLIENTID": "0"
        }
        return config_json