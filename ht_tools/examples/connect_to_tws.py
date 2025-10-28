import time
from ht_tools.utils import load_config
from ht_tools.utils.logger import LoggerManager
from ht_tools.core.connector import IBKRConnection

if __name__ == "__main__":
    # If __main__ entry point, LoggerManager must be initialized
    config_json = load_config()
    LoggerManager.initialize(config_json.get("logging"))
    
    # Get IBKR Connection details and use a context manager to connect
    # Context will automatically call open_connection() and close_connection() methods
    ibkr_info = config_json.get("IBKR", {})
    with IBKRConnection(ibkr_info) as ib:
        print("Sleeping for 2 seconds while connected to TWS/IB Gateway...")
        time.sleep(2)