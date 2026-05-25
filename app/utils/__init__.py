import json
import os

from pathlib import Path
from importlib.resources import files


def _resolve_config_path():
    # Priority: explicit env var, local working directory, packaged default.
    override_path = os.getenv("HT_IBKR_CONFIG_FILE")
    if override_path:
        override = Path(override_path).expanduser()
        if override.exists() and override.is_file():
            return override
        try:
            override.parent.mkdir(parents=True, exist_ok=True)
            override.write_text(_packaged_config_path().read_text(encoding="utf-8"), encoding="utf-8")
            return override
        except Exception:
            pass

    # Prefer repository-local config files when running from source.
    local_candidates = [
        Path.cwd() / "config.json",
        Path.cwd() / "app" / "config.json",
    ]
    for local_config in local_candidates:
        if local_config.exists() and local_config.is_file():
            return local_config

    user_config = _ensure_user_config_file()
    if user_config is not None:
        return user_config

    return _packaged_config_path()


def _packaged_config_path():
    return files("app").joinpath("config.json")


def _default_user_config_path() -> Path:
    if os.name == "nt":
        base_dir = Path(os.getenv("APPDATA", str(Path.home())))
        return base_dir / "HT-IBKR-Integrations" / "config.json"
    return Path.home() / ".config" / "ht-ibkr-integrations" / "config.json"


def _ensure_user_config_file() -> Path | None:
    user_config_path = _default_user_config_path()
    if user_config_path.exists() and user_config_path.is_file():
        return user_config_path

    try:
        user_config_path.parent.mkdir(parents=True, exist_ok=True)
        user_config_path.write_text(_packaged_config_path().read_text(encoding="utf-8"), encoding="utf-8")
        return user_config_path
    except Exception:
        return None


def get_active_config_path() -> str:
    return str(_resolve_config_path())


def _load_config_data() -> dict:
    config_path = _resolve_config_path()
    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)

def load_config_logging() -> json:
    try:
        return _load_config_data().get("logging", {
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
        return _load_config_data().get("database", {
            "filename": "database/htibkr.db",
            "tabledefinitions": "app/dto/table_definitions.sql"
        })
    except Exception as e:
        # Fallback config.json if non existing filr in project root
        config_json = {
            "filename": "database/htibkr.db",
            "tabledefinitions": "app/dto/table_definitions.sql"
        }
        return config_json
    
def load_config_ibapi() -> json:
    try:
        return _load_config_data().get("IBKR", {
            "HOST": "localhost",
            "PORT": 7497,
            "CLIENTID": "0",
            "ACCOUNTID": "DUMXXXXXX"
        })
    except Exception as e:
        # Fallback config.json if non existing filr in project root
        config_json = {
            "HOST": "localhost",
            "PORT": 7497,
            "CLIENTID": "0",
            "ACCOUNTID": "DUMXXXXXX"
        }
        return config_json
    
def load_config_scheduler() -> json:
    default_scheduler = {
        "scanner": {
            "enabled": True,
            "interval": 60
        },
        "watcher": {
            "enabled": True,
            "interval": 60
        },
        "portfolio_watcher": {
            "enabled": False,
            "interval": 60
        },
        "execution_watcher": {
            "enabled": False,
            "interval": 60
        }
    }

    try:
        scheduler = _load_config_data().get("scheduler", {})
        merged_scheduler = dict(default_scheduler)

        for section_name, default_section in default_scheduler.items():
            section = scheduler.get(section_name, {})
            if isinstance(section, dict):
                merged_section = dict(default_section)
                merged_section.update(section)
                merged_scheduler[section_name] = merged_section

        return merged_scheduler
    except Exception as e:
        # Fallback config.json if non existing filr in project root
        return default_scheduler