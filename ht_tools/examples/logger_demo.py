"""
Demo script for testing the LoggerManager class.

This script demonstrates how to use the LoggerManager class to initialize logging
and log messages with different levels of detail.

Usage:
    python demo_logger.py

Requirements:
    - ht_tools.utils module with load_config function
    - ht_tools.utils.logger module with LoggerManager class

This script will:
    1. Load configuration from a JSON file using load_config function.
    2. Initialize the logger using LoggerManager.
    3. Log a success message.
    4. Test logging of exceptions with and without traceback details.
    5. Wait for user input before exiting.
"""

from ht_tools.utils import load_config
from ht_tools.utils.logger import LoggerManager

if __name__ == '__main__':
    config_json = load_config()

    LoggerManager.initialize(config_json.get("logging"))
    logger = LoggerManager.get_logger()
    logger.info("Logging initialized successfully.")

    # Example of logging without a full traceback
    try:
        raise RuntimeError('Testing basic logger with exception')
    except RuntimeError as e:
        logger.exception("Caught Basic RuntimeError", exc_info=False)  # No details in log trace
        
    # Example of logging with a full traceback
    try:
        raise RuntimeError('Testing full logger with exception')
    except RuntimeError as e:
        logger.exception("Caught Full trace RuntimeError", exc_info=True)  # Runtime details in log using traceback
        
    input("Hit ENTER to exist example...")        
    