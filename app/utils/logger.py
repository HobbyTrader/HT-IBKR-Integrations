import logging
import os
from datetime import datetime
from pathlib import Path 

class LoggerManager:
    """
    A utility class for managing logging in an application.

    This class is designed to be used as a singleton, where all methods are class methods.
    It should not be instantiated directly. Instead, use the class methods to configure
    and access the logger.

    Example:
        LoggerManager.initialize(config)
        logger = LoggerManager.get_logger()
        logger.info("This is a log message")
    """    
    
    _initialized = False
    _logger_name = "IBKRIntegration"

    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_CONSOLE_LEVEL = "WARNING"
    FILE_FORMAT = f"%(asctime)s.%(msecs)03d | (%(threadName)s) | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
    CONSOLE_FORMAT = '%(levelname)s | %(message)s'
    TIME_FORMAT = "%Y-%m-%d_%H:%M:%S"   
    TIMESTAMP_FOR_FILE_NAME = "%Y-%m-%d_%H"    # use "%Y-%m-%d_%H:%M:%S" for a file every second
    
    @classmethod
    def initialize(cls, config: dict):
        """
        Set up logging once per application. Public function.

        Args:
            config (dict): A dictionary containing logging configuration.
                - logpath (str): The path to the log directory. Defaults to "LOG".
                - loglevel (str): The log level for file logging. Defaults to "INFO".
                - consolelevel (str): The log level for console logging. Defaults to "WARNING".

        Raises:
            Exception: If an error occurs during logger initialization.
        """ 
        if cls._initialized:
            return  # avoid double setup

        try:
            cls._create_log_directory(config.get("logpath", "LOG"))
            log_file = cls._create_log_file(config)
            cls._configure_logger(config, log_file)
            cls._initialized = True
        except Exception as e:
            print(f"Error initializing logger: {e}")    

    @classmethod
    def get_logger(cls):
        """
        Return a named logger instance.

        Returns:
            logging.Logger: The logger instance.
        """        
        return logging.getLogger(cls._logger_name)    

            
    @classmethod
    def _create_log_directory(cls, log_path: str):
        """
        Create the log directory if it does not exist. Private function.

        Args:
            log_path (str): The path to the log directory.

        Raises:
            OSError: If an error occurs during directory creation.
        """        
        log_dir = Path(log_path)
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"HT-TOOLS: Failed to create log directory {log_dir}: {e}") from e     

    @classmethod
    def _create_log_file(cls, config: dict):
        """
        Create the log file name based on the current timestamp and log_directory. Private function.

        Args:
            config (dict): A dictionary containing logging configuration.

        Returns:
            Path: The path to the log file.
        """        
        timestamp = datetime.now().strftime(cls.TIMESTAMP_FOR_FILE_NAME)
        log_dir = Path(config.get("logpath", "LOG"))
        return log_dir / f"{cls._logger_name}.{timestamp}.log"
        
    @classmethod
    def _configure_logger(cls, config: dict, log_file: Path):
        """
        Configure the logger with file and console handlers. Private function.

        Args:
            config (dict): A dictionary containing logging configuration.
            log_file (Path): The path to the log file.
        """
        log_level = getattr(logging, config.get("loglevel", cls.DEFAULT_LOG_LEVEL).upper(), logging.INFO)
        console_level = getattr(logging, config.get("consolelevel", cls.DEFAULT_CONSOLE_LEVEL).upper(), logging.WARNING)

        logger = logging.getLogger(cls._logger_name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()  # avoid duplicates

        cls._configure_file_handler(logger, log_file, log_level)
        cls._configure_console_handler(logger, console_level)

        logger.propagate = False
        logger.info(f"Logger initialized. Log file: {log_file}")  

    @classmethod
    def _configure_file_handler(cls, logger: logging.Logger, log_file: Path, log_level: int):
        """
        Configure the file handler for the logger. Private function.

        Args:
            logger (logging.Logger): The logger instance.
            log_file (Path): The path to the log file.
            log_level (int): The log level for the file handler.
        """        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(cls.FILE_FORMAT, datefmt=cls.TIME_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)           
        
    @classmethod
    def _configure_console_handler(cls, logger: logging.Logger, console_level: int):
        """
        Configure the console handler for the logger. Private function.

        Args:
            logger (logging.Logger): The logger instance.
            console_level (int): The log level for the console handler.
        """        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter(cls.CONSOLE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)    
        
           