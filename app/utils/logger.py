import logging
import logging.config
import os
from app.utils import load_config_logging


class LoggerManager:   
    _initialized = False   
    
    def __init__(cls, log_filename: str = None):
        if cls._initialized:
            return 

        # Get the config.json if exists, fallback on hard-coded values
        log_params = load_config_logging()
        
        # Use provided filename, fallback to config file value, then default
        if log_filename:
            log_params["logname"] = log_filename
        
        os.makedirs(log_params.get("logpath"), exist_ok=True)
        # Define the configuration dictionary
        log_config = {
            "version": 1,
            "disable_existing_loggers": False, # Keep existing loggers
            "formatters": {
                "precise_formatter": {
                    "format": "{asctime} | {levelname} | {name} | {filename}:{lineno} | {message} ",
                    "style": "{",
                },
                "simple_console_formatter": {
                    "format": "{levelname}|{filename}:{lineno}|{message}",
                    "style": "{",
                },            
            },
            "handlers": {
                "minute_rotating_file_handler": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "formatter": "precise_formatter",
                    "filename": os.path.join(log_params.get("logpath"), log_params.get("logname")),
                    "when": "m",                                        # Rotate minute interval
                    "interval": 1,                                      # Rotate every 1 minute   
                    "backupCount": log_params.get("backupcount"),       # Keep only 5 by default histrical log files
                    "level": log_params.get("loglevel", "DEBUG"),
                },
                "console_handler": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple_console_formatter",
                    "level": log_params.get("consolelevel", "WARNING"),
                },            
            },
            "root": {
                # Use the rotating file handler for everything
                "handlers": ['minute_rotating_file_handler', 'console_handler'],
                "level": log_params.get("loglevel", "DEBUG"),
            },
        }

        logging.config.dictConfig(log_config)  
        cls._initialized = True

    @classmethod
    def add_file_handler(cls, log_filename: str) -> str:
        """Attach an extra file handler using logging settings from config.json."""
        log_params = load_config_logging()
        log_path = log_params.get("logpath", "LOG")
        full_path = os.path.abspath(os.path.join(log_path, log_filename))

        os.makedirs(log_path, exist_ok=True)

        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.FileHandler) and getattr(handler, "baseFilename", None) == full_path:
                return full_path

        file_handler = logging.FileHandler(full_path)
        file_handler.setLevel(log_params.get("loglevel", "DEBUG"))
        file_handler.setFormatter(
            logging.Formatter(
                "{asctime} | {levelname} | {name} | {filename}:{lineno} | {message} ",
                style="{",
            )
        )
        root_logger.addHandler(file_handler)
        return full_path
    
# Automatically create the logger manager on import.
LoggerManager()