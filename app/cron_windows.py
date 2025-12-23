import logging

from pathlib import Path
import platform

from app.utils.logger import LoggerManager

LoggerManager(log_filename="cron_windows.log")
logger = logging.getLogger(__name__)

def generate_windows_powershell_lines(schedules):
    """
    Génère des commandes PowerShell New-ScheduledTaskTrigger / Register-ScheduledTask.
    Plus précis que schtasks pour des schedules complexes.
    """
    commands = []
    for row in schedules:
        if row["os"].lower() != "windows":
            continue

        task_name = row["task_name"]        # ex: "MyPythonJob"
        schedule_desc = row["schedule_desc"]  # ex: "DAILY", "HOURLY", "MINUTE"
        command = row["command"]            # ex: "C:\\Python\\python.exe C:\\path\\script.py --foo bar"
        start_time = row.get("start_time", "10:00")  # ex: "10:00"

        # Action: lancer le script Python
        action = f'New-ScheduledTaskAction -Execute "{command.split()[0]}" -Argument "{ " ".join(command.split()[1:]) }"' 
        
        # Trigger selon schedule_desc
        trigger_map = {
            "DAILY": f'New-ScheduledTaskTrigger -Daily -At "{start_time}"',
            "HOURLY": f'New-ScheduledTaskTrigger -Once -At "{start_time}" -RepetitionInterval (New-TimeSpan -Hours 1)',
            "MINUTE": f'New-ScheduledTaskTrigger -Once -At "{start_time}" -RepetitionInterval (New-TimeSpan -Minutes 5)',
            # Ajoute d'autres mappings selon tes besoins
        }
        
        trigger = trigger_map.get(schedule_desc.upper(), trigger_map["DAILY"])
        
        # Principal script PowerShell
        ps_cmd = f'''
$action = {action}
$trigger = {trigger}
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Principal $principal -Force
'''
        commands.append(ps_cmd.strip())
    
    return commands

def write_windows_powershell_file(commands, output_file: str):
    """
    Génère un script .ps1 à exécuter (clic droit > "Exécuter avec PowerShell" ou via terminal).
    """
    header = '''# PowerShell script généré automatiquement pour créer les tâches planifiées
# Exécuter en tant qu'administrateur
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
'''
    
    content = header + "\n\n".join(commands) + "\n\nWrite-Host 'Toutes les tâches ont été créées avec succès.'"
    Path(output_file).write_text(content, encoding="utf-8")

if __name__ == "__main__":
    
    schedules = load_schedules_from_db(db_path)  # Fonction du message précédent

    if platform.system() == "Windows":
        ps_lines = generate_windows_powershell_lines(schedules)
        write_windows_powershell_file(ps_lines, "create_tasks.ps1")
        print("✅ Script PowerShell généré : create_tasks.ps1")
        print("💡 À exécuter : Clic droit > 'Exécuter avec PowerShell' (en admin)")
        print("   Ou via terminal : powershell -ExecutionPolicy Bypass -File create_tasks.ps1")
