import json

from importlib.resources import files

_config_path = files('app').joinpath('config.json')

def load_config_cron() -> json:
    try:
        with open(_config_path) as file:
            return json.load(file).get("cron", {
            "cron_output_file": "macos_cron_jobs.txt",
            "cron_output_path": "/Users/greg/Dev/HTTrader/HT-IBKR-Integrations/cron_script",
            "cron_script_path": "/Users/greg/Dev/HTTrader/HT-IBKR-Integrations/",
            "cron_script_name": "app.main",
            "cron_script_params": ""
        })
    except Exception as e:
        # Fallback config.json if non existing filr in project root
        config_json = {
            "cron_output_file": "macos_cron_jobs.txt",
            "cron_output_path": "/Users/greg/Dev/HTTrader/HT-IBKR-Integrations/cron_script",
            "cron_script_path": "/Users/greg/Dev/HTTrader/HT-IBKR-Integrations/",
            "cron_script_name": "app.main",
            "cron_script_params": ""
        }
        return config_json