import logging

from pathlib import Path
import platform

from app.__init__ import load_config_cron
from app.dto.strategie_dto import StrategieDTO
from app.utils.logger import LoggerManager

LoggerManager(log_filename="cron_macos.log")
logger = logging.getLogger(__name__)

config = load_config_cron()
command_output_file = config["cron_output_file"]
command_output_path = config["cron_output_path"]
command_path = config["cron_script_path"]
command_name = config["cron_script_name"]
command_params = config["cron_script_params"]
command_script_path = f"{command_path}{command_name} {command_params}"
# TODO: Tester si on sait forcer le path du script à l'exécution ou s'il faut faire un cd d'abord!!!!

def load_schedules_from_db():
    schedules = []
    strategies_dto = StrategieDTO()
    strategies = strategies_dto.get_active_strategies()
    for strategy in strategies:
        logger.info(f"Active Strategy: {strategy}") 
        schedules.append({
            "strategy_id": strategy.id,
            "strategy_name": strategy.name,
            "cron_expr": "45 9 * * 1-5",  #strategy.build_cron_schedules(),})
            "command": f"python3 {command_script_path}",
            "tags": strategy.tags})
                         
    return schedules

def generate_macos_crontab_lines(schedules):
    """
    Retourne une liste de lignes crontab pour macOS.
    On suppose que chaque ligne a un champ 'cron_expr' et 'command'.
    """
    lines = []
    
    for row in schedules:
        logger.info(f"Processing schedule for strategy: {row['strategy_name']}")
        cron_expr = row["cron_expr"]         # ex: "0 * * * *"
        command = row["command"]             # ex: "/usr/bin/python3 /path/to/script.py"
        tags = row.get("tags", [])
        lines.append(f"{cron_expr} {command} {','.join(str(tag) for tag in tags)} True")
    return lines

def write_macos_crontab_file(lines, output_file: str):
    """
    Génère un fichier texte que tu pourras charger dans crontab :
    crontab my_crontab.txt
    """
    content = "\n".join(lines) + "\n"
    Path(output_file).write_text(content, encoding="utf-8")

if __name__ == "__main__":
    schedules = load_schedules_from_db()

    if platform.system() == "Darwin":
        cron_lines = generate_macos_crontab_lines(schedules)
        write_macos_crontab_file(cron_lines, "generated_crontab.txt")
        print("Crontab généré dans generated_crontab.txt (à installer avec `crontab generated_crontab.txt`).")
