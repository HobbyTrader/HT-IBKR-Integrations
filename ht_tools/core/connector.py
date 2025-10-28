import threading
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.ticktype import *

from ht_tools.utils import load_config
from ht_tools.utils.logger import LoggerManager

class IBKRConnection(EWrapper, EClient):
    """ A minimal, thread-safe wrapper around the IBKR TWS API.
        EWrapper: defines callback function to get events from TWS
        EClient: defines methods to send requests to TWS
    """

    def __init__(self, config: dict):
        EClient.__init__(self, wrapper=self)

        # Validate and load IBKR connection info
        self.HOST = config.get("HOST", "127.0.0.1")      # Sets default value for HOST if not specified
        self.PORT = config.get("PORT", 7497)             # Sets default value for PORT if not specified (default is paper trading)
        self.CLIENT_ID = config.get("CLIENT_ID", 1)      # Sets default client_id if not specified

        self.logger = LoggerManager.get_logger()         
        self.logger.info(f"Logging initialized successfully.") 
        self.connection_thread = None
        self._is_connected = False

    # ------------------------------------------------------
    # Connection management
    # -----------------------------------------------------
    def open_connection(self):
        """Connect to TWS or IB Gateway and start the API loop."""
        if self.isConnected():
            self.logger.warning("IBKR already connected.")
            return

        try:
            self.connect(self.HOST, self.PORT, self.CLIENT_ID)

            self.connection_thread = threading.Thread(target=self.run, daemon=True)
            self.connection_thread.start()

            # Give the client a brief moment to establish connection
            time.sleep(1)
            # Connection will be real only when nextValidId callback is received
            #self._is_connected = self.isConnected()
            #if self._is_connected:
            #    self.logger.info(f"Connected to IBKR TWS at {self.HOST}:{self.PORT} (Client ID: {self.CLIENT_ID})")
            #else:
            #    self.logger.error("IBKR connection attempt failed.")

        except Exception as e:
            self.logger.exception(f"Error while connecting to IBKR: {e}", exc_info=True)

    def close_connection(self):
        """Disconnect cleanly from TWS or IB Gateway."""
        try:
            if self.isConnected():
                self.disconnect() # Call back will set the _is_connected flag to False and log the event
                # self._is_connected = False
                # self.logger.info(f"Disconnected from IBKR TWS at {self.HOST}:{self.PORT} (Client ID: {self.CLIENT_ID})")
            else:
                self.logger.warning("Attempted to disconnect, but not currently connected.")

        except Exception:
            self.logger.exception("Failed to disconnect from IBKR.", exc_info=True)

    # -----------------------------------------------------
    # Context manager support
    # -----------------------------------------------------
    def __enter__(self):
        self.open_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    # -----------------------------------------------------
    # Optional destructor (not strictly required)
    # -----------------------------------------------------
    def __del__(self):
        if self.isConnected():
            self.close_connection()

    # -----------------------------------------------------
    # Callback overrides from EWrapper
    # -----------------------------------------------------
    def connectionClosed(self):
        self.logger.warning(f"Connection to TWS closed. HOST: {self.HOST}, PORT: {self.PORT}, CLIENT_ID: {self.CLIENT_ID}")

    def nextValidId(self, orderId: int):
        self.logger.info(f"Next valid order ID: {orderId}")

    def error(self, *args):
        """Override the error callback to log errors."""
        errorCode = args[2] if len(args) > 2 else None
        if errorCode in [1100, 2110]:
            self.logger.info(f"IBKR Error event: {args} -> (reqId, timestamp, errorCode, errorString, advancedOrderRejectionJson)")
        elif errorCode in [1101, 1102, 2103, 2104, 2105, 2106, 2157, 2158]:
            self.logger.warning(f"IBKR Error event: {args} -> (reqId, timestamp, errorCode, errorString, advancedOrderRejectionJson)")
        elif errorCode in range(200, 1000):
            self.logger.error(f"IBKR Error event: {args} -> (reqId, timestamp, errorCode, errorString, advancedOrderRejectionJson)")
        else:
            self.logger.critical(f"IBKR Error event: {args} -> (reqId, timestamp, errorCode, errorString, advancedOrderRejectionJson)")
    
    # Severity	    Typical Codes	                    Meaning
    # ------------- --------------------------------    ----------------------------------------
    # Critical	    1100, 2110	                        Lost connection to TWS or IB gateway
    # Warning	    1101, 1102, 2103–2106, 2157–2158	Temporary data farm interruptions
    # Non-critical	200–999	                            Request errors, pacing violations
    # Info	        2104, 2158	                        “Connection is OK” or “Restored” messages


# -----------------------------------------------------
# Main entry point used for debugging - remove for prodcuction
# -----------------------------------------------------
if __name__ == "__main__":
    # If __main__ entry point, LoggerManager must be initialized
    config_json = load_config()
    LoggerManager.initialize(config_json.get("logging"))
    
    # Get IBKR Connection details and use a context manager to connect
    # Context will automatically call open_connection() and close_connection() methods
    ibkr_info = config_json.get("IBKR", {})
    with IBKRConnection(ibkr_info) as ib:
        time.sleep(5)




