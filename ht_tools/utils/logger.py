import logging.config
import os
from ht_tools.utils import load_config


class LoggerManager:   
    _initialized = False
    LOG_FILE_NAME = f"HT_TOOLS.log"
    # FULL_LOG_PATH = os.path.join(LOG_FOLDER, LOG_FILE_NAME)     
    
    def __init__(cls, backup_count=5):
        if cls._initialized:
            return 

        # Get the config.json if exists, fallback on hard-coded values
        log_params = load_config().get("logging", {
            "logpath": "LOG",
            "logname": "HT_TOOLS.log",
            "loglevel": "DEBUG",
            "consolelevel": "WARNING",
            "backupcount": 10
        })
        
        os.makedirs(log_params.get("logpath"), exist_ok=True)
        # Define the configuration dictionary
        log_config = {
            'version': 1,
            'disable_existing_loggers': False, # Keep existing loggers
            'formatters': {
                'precise_formatter': {
                    'format': '{asctime} | {levelname} | {name} | {filename}:{lineno} | {message} ',
                    'style': '{',
                },
                'simple_console_formatter': {
                    'format': '{levelname}|{filename}:{lineno}|{message}',
                    'style': '{',
                },            
            },
            'handlers': {
                'minute_rotating_file_handler': {
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'formatter': 'precise_formatter',
                    'filename': os.path.join(log_params.get("logpath"), log_params.get("logname")),
                    'when': 'm',                                        # Rotate minute interval
                    'interval': 1,                                      # Rotate every 1 minute   
                    'backupCount': log_params.get("backupcount"),       # Keep only 5 by default histrical log files
                    'level': 'DEBUG',
                },
                'console_handler': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple_console_formatter',
                    'level': 'WARNING',
                },            
            },
            'root': {
                # Use the rotating file handler for everything
                'handlers': ['minute_rotating_file_handler', 'console_handler'],
                'level': 'DEBUG',
            },
        }

        logging.config.dictConfig(log_config)  
        cls._initialized = True
    
# Automaticallt create the logger manager on import.
LoggerManager()