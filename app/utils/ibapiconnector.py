import threading
import time
import logging

from ibapi.wrapper import EWrapper
from ibapi.client import EClient

from app.utils import load_config_ibapi

logger = logging.getLogger(__name__)

COMMON_ORDER_REJECT_CODES = {
    201,   # Order rejected
    203,   # Security not available / restrictions
    321,   # Validation error
    322,   # Processing error
    2010,  # Generic order reject
    10147, # Order rejected by system/risk checks
    10148, # Order rejected/held for risk checks
}

class IBApiConnector(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        config = load_config_ibapi()
        
        # Validate and load IBKR connection info
        self.HOST = config.get("HOST", "127.0.0.1")      # Sets default value for HOST if not specified
        self.PORT = int(config.get("PORT", 7497))             # Sets default value for PORT if not specified (default is paper trading)
        self.CLIENT_ID: int = int(config.get("CLIENTID", 1))       # Sets default client_id if not specified
       
        self.connection_thread = None
        self._is_connected = False
        self.orderId = None
        self._order_id_ready = threading.Event()
        self._order_id_lock = threading.Lock()
        self._request_id_lock = threading.Lock()
        self._request_id = 1

    # ------------------------------------------------------
    # Connection management
    # -----------------------------------------------------
    def open_connection(self, clientId: int = None):
        """Connect to TWS or IB Gateway and start the API loop."""
        if self.isConnected():
            logger.warning("IBKR already connected.")
            return

        # Use parameter if provided, else fallback to instance attribute
        effective_client_id = clientId if clientId is not None else self.CLIENT_ID
        
        try:
            self.connect(self.HOST, self.PORT, effective_client_id)
            
            self.CLIENT_ID = effective_client_id

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
            logger.exception(f"Error while connecting to IBKR: {e}", exc_info=True)

    def close_connection(self):
        """Disconnect cleanly from TWS or IB Gateway."""
        try:
            if self.isConnected():
                self.disconnect() # Call back will set the _is_connected flag to False and log the event
                # self._is_connected = False
                logger.info(f"Disconnected from IBKR TWS at {self.HOST}:{self.PORT} (Client ID: {self.CLIENT_ID})")
            else:
                logger.warning("Attempted to disconnect, but not currently connected.")

        except Exception:
            logger.exception("Failed to disconnect from IBKR.", exc_info=True)

    # -----------------------------------------------------
    # Context manager support
    # -----------------------------------------------------
    def __enter__(self):
        self.open_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()
        return False

    # -----------------------------------------------------
    # Optional destructor (not strictly required)
    # -----------------------------------------------------
    # def __del__(self):
    #     if self.isConnected():
    #         self.close_connection()

    # -----------------------------------------------------
    # Callback overrides from EWrapper
    # -----------------------------------------------------
    def connectionClosed(self):
        logger.warning(f"Connection to TWS closed. HOST: {self.HOST}, PORT: {self.PORT}, CLIENT_ID: {self.CLIENT_ID}")

    def nextValidId(self, orderId: int):
        with self._order_id_lock:
            self.orderId = orderId
        with self._request_id_lock:
            if self._request_id <= orderId:
                self._request_id = orderId + 1
        self._order_id_ready.set()
        logger.info(f"Next valid order ID: {orderId}")
    
    def nextId(self, timeout: float = 10.0):
        if not self._order_id_ready.wait(timeout):
            raise RuntimeError("IBKR order id not initialized yet. nextValidId callback was not received.")

        with self._order_id_lock:
            if self.orderId is None:
                raise RuntimeError("IBKR order id is unavailable.")
            self.orderId += 1
            return self.orderId

    def nextRequestId(self):
        with self._request_id_lock:
            req_id = self._request_id
            self._request_id += 1
        return req_id

    def _is_order_reject_error(self, error_code: int | None, error_string: str) -> bool:
        if error_code in COMMON_ORDER_REJECT_CODES:
            return True

        message = (error_string or "").lower()
        reject_tokens = [
            "rejected",
            "not allowed",
            "insufficient",
            "buying power",
            "margin",
            "prohibited",
            "not available for trading",
            "outside regular trading hours",
            "permission",
            "not subscribed",
        ]
        return any(token in message for token in reject_tokens)

    def _parse_error_args(self, *args):
        req_id = None
        error_time = None
        raw_error_code = None
        error_string = ""
        advanced_order_rejection_json = None

        # IBKR can call either:
        # 1) error(reqId, errorCode, errorString)
        # 2) error(reqId, errorTime, errorCode, errorString, advancedOrderRejectJson)
        if len(args) >= 5:
            req_id = args[0]
            error_time = args[1]
            raw_error_code = args[2]
            error_string = args[3]
            advanced_order_rejection_json = args[4]
        elif len(args) == 4:
            req_id = args[0]
            raw_error_code = args[1]
            error_string = args[2]
            advanced_order_rejection_json = args[3]
        elif len(args) == 3:
            req_id = args[0]
            raw_error_code = args[1]
            error_string = args[2]
        elif len(args) == 2:
            req_id = args[0]
            raw_error_code = args[1]
        elif len(args) == 1:
            req_id = args[0]

        if error_string is None:
            error_string = ""
        elif not isinstance(error_string, str):
            error_string = str(error_string)

        try:
            error_code = int(raw_error_code) if raw_error_code is not None else None
        except (TypeError, ValueError):
            error_code = None

        return req_id, error_time, error_code, error_string, advanced_order_rejection_json

    def error(self, *args):
        """Override the error callback to log errors."""
        req_id, error_time, error_code, error_string, advanced_order_rejection_json = self._parse_error_args(*args)

        is_reject = self._is_order_reject_error(error_code, error_string)

        if is_reject:
            logger.error(
                "IBKR ORDER REJECT | reqId=%s errorTime=%s errorCode=%s errorString=%s advancedReject=%s",
                req_id,
                error_time,
                error_code,
                error_string,
                advanced_order_rejection_json,
            )

            # Unblock waiting order events when a rejection is received.
            if hasattr(self, "order_events") and req_id in getattr(self, "order_events", {}):
                self.order_events[req_id].set()
            return

        match error_code:
            # INFO
            case 165 | 2104 | 2106 | 2110 | 2119 | 2152 | 2158:
                logger.info(
                    "IBKR Info event: reqId=%s errorTime=%s errorCode=%s errorString=%s advancedReject=%s",
                    req_id,
                    error_time,
                    error_code,
                    error_string,
                    advanced_order_rejection_json,
                )
            # WARNING
            case range(1100, 1300) | 2103 | 2105 | 2137:
                logger.warning(
                    "IBKR Warning event: reqId=%s errorTime=%s errorCode=%s errorString=%s advancedReject=%s",
                    req_id,
                    error_time,
                    error_code,
                    error_string,
                    advanced_order_rejection_json,
                )
            # ERROR
            case range(100, 1000) | range(2100, 11000):
                logger.error(
                    "IBKR Error event: reqId=%s errorTime=%s errorCode=%s errorString=%s advancedReject=%s",
                    req_id,
                    error_time,
                    error_code,
                    error_string,
                    advanced_order_rejection_json,
                )
            case _:
                logger.critical(
                    "IBKR Critical event: reqId=%s errorTime=%s errorCode=%s errorString=%s advancedReject=%s",
                    req_id,
                    error_time,
                    error_code,
                    error_string,
                    advanced_order_rejection_json,
                )
    
    # Severity	    Typical Codes	                    Meaning
    # ------------- --------------------------------    ----------------------------------------
    # Critical	    1100, 2110	                        Lost connection to TWS or IB gateway
    # Warning	    1101, 1102, 2103–2106, 2157–2158	Temporary data farm interruptions
    # Non-critical	200–999	                            Request errors, pacing violations
    # Info	        2104, 2158	                        “Connection is OK” or “Restored” messages

    
    

    