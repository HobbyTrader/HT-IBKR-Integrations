# examples/example_usage.py

import logging
from ht_tools.utils.logger import LoggerManager

# Always place this line at the top of you module to use imported LoggerManager configuration
log = logging.getLogger(__name__)

if __name__ == "__main__":
    print("Logging messages. Check the 'application_logs' folder for the file output.")
    
    # Demonstrate logging at all levels
    # DEBUG won't show up by default because the root level is set to INFO
    log.debug("This is a debug message (You shouldn't see this in INFO mode).") 
    log.info("This is an info message.")
    log.warning("This is a warning message.")
    log.error("This is an error message.")
    log.critical("This is a critical message.")
    log.info("Script finished successfully.")