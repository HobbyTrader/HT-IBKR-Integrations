import logging
import os
from datetime import datetime
from pathlib import Path

class LoggerManager:
    _initialized = False
    _logger_name = "IBKRIntegration"
    
    @classmethod
    def initialize(cls, config: dict):
        """Set up logging once per application."""
        if cls._initialized:
            return  # avoid double setup

        log_path = config.get("logpath", "LOG")                     # default to LOG if not specified in config.json
        # log_level = config.get("loglevel", "INFO").upper()          # Fiel logging : default to INFO if not specified in config.json
        # console_level = config.get("consolelevel", "WARNING").upper()   # Console setting : default to WARNING if not specified in config.json
        log_level = getattr(logging, config.get("loglevel", "INFO").upper(), logging.INFO)
        console_level = getattr(logging, config.get("consolelevel", "WARNING").upper(), logging.WARNING)

        # Create log directory
        log_dir = Path(log_path)
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"HT-TOOLS: Failed to create log directory {log_dir}: {e}") from e


        timestamp = datetime.now().strftime("%Y%m%d_%H")    # One file for each hour -> %H%M%S for each second
        log_file = log_dir / f"{cls._logger_name}.{timestamp}.log"

        # Format strings
        file_format = f"%(asctime)s.%(msecs)03d | (%(threadName)s) | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
        console_format = f'%(levelname)s | %(message)s'
        time_format = "%Y-%m-%d_%H:%M:%S"

        # --- Create the main logger ---
        logger = logging.getLogger(cls._logger_name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()  # avoid duplicates

        # --- File handler ---
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)    
        file_formatter = logging.Formatter(file_format, datefmt=time_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # --- Console handler ---
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter(console_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        logger.propagate = False
        logger.info(f"Logger initialized. Log file: {log_file}")

        cls._initialized = True    
        
    @classmethod
    def get_logger(cls):
        """Return a named logger (after initialization)."""
        return logging.getLogger(cls._logger_name)
    
