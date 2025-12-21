import logging

from pathlib import Path
import platform

from app.dto.strategie_dto import StrategieDTO

logger = logging.getLogger(__name__)

def load_schedules_from_db():
    schedules = []
    strategies_dto = StrategieDTO()
    strategies = strategies_dto.getActiveStrategies()
    for strategy in strategies:
        logger.info(f"Active Strategy: {strategy}") 
        schedules.append({
            "strategy_id": strategy.id,
            "strategy_name": strategy.name,
            "cron_expr": strategy.build_cron_schedules(),
            "command": ,        })
        
    return schedules
#     conn = sqlite3.connect(db_path)
#     conn.row_factory = sqlite3.Row
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM schedules")
#     rows = cur.fetchall()
#     conn.close()
#     return rows

def generate_macos_crontab_lines(schedules):
    """
    Retourne une liste de lignes crontab pour macOS.
    On suppose que chaque ligne a un champ 'cron_expr' et 'command'.
    """
    lines = []
    for row in schedules:
        if row["os"].lower() != "macos":
            continue
        cron_expr = row["cron_expr"]         # ex: "0 * * * *"
        command = row["command"]             # ex: "/usr/bin/python3 /path/to/script.py"
        lines.append(f"{cron_expr} {command}")
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
