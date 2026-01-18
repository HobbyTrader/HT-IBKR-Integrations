import unittest
from unittest.mock import Mock, patch, MagicMock, call
import threading
import time
import itertools

from app.utils.ibapiconnector import IBApiConnector
from vendor.ibapi.client import EClient
from vendor.ibapi.wrapper import EWrapper


class TestIBApiConnector(unittest.TestCase):
    """Test cases for IBApiConnector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connector = IBApiConnector()
        
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.connector, 'connection_thread') and self.connector.connection_thread:
            self.connector.close_connection()
    
    # ============================================================================
    # INITIALIZATION TESTS
    # ============================================================================
    
    def test_initialization(self):
        """Test that IBApiConnector initializes correctly."""
        self.assertIsInstance(self.connector, EClient)
        self.assertIsInstance(self.connector, EWrapper)
        self.assertIsNone(self.connector.connection_thread)  # ✅ Fixed
        self.assertFalse(self.connector._is_connected)
        
    def test_inherits_from_eclient(self):
        """Test that IBApiConnector inherits from EClient."""
        self.assertTrue(isinstance(self.connector, EClient))
        
    def test_inherits_from_ewrapper(self):
        """Test that IBApiConnector inherits from EWrapper."""
        self.assertTrue(isinstance(self.connector, EWrapper))
    
    # ============================================================================
    # CONNECTION TESTS
    # ============================================================================
    
    @patch('app.utils.ibapiconnector.EClient.connect')
    @patch('app.utils.ibapiconnector.EClient.run')
    def test_connect_success(self, mock_run, mock_connect):
        """Test successful connection to IBKR."""
        mock_connect.return_value = None
        mock_run.side_effect = lambda: time.sleep(10)
        
        self.connector.open_connection(1)
        
        mock_connect.assert_called_once_with("localhost", 7497, 1)
        self.assertIsNotNone(self.connector.connection_thread)
        time.sleep(0.1)
        self.assertTrue(self.connector.connection_thread.is_alive())
        
    @patch('app.utils.ibapiconnector.EClient.connect')
    def test_connect_default_parameters(self, mock_connect):
        """Test connection with default parameters."""
        mock_connect.return_value = None
        
        self.connector.open_connection()
        
        # Should use default CLIENT_ID from config
        mock_connect.assert_called_once_with("localhost", 7497, 0)
        self.assertIsNotNone(self.connector.connection_thread)
    
    # ============================================================================
    # DISCONNECTION TESTS
    # ============================================================================
    
    @patch('app.utils.ibapiconnector.EClient.isConnected')
    @patch('app.utils.ibapiconnector.EClient.disconnect')
    @patch('app.utils.ibapiconnector.EClient.connect')
    def test_disconnect(self, mock_connect, mock_disconnect, mock_is_connected):
        """Test disconnection from IBKR."""
        mock_connect.return_value = None
        mock_is_connected.side_effect = itertools.chain([False], itertools.repeat(True))
        
        # First connect
        self.connector.open_connection(0)
        self.assertIsNotNone(self.connector.connection_thread)
        
        # Then disconnect
        self.connector.close_connection()
        
        mock_disconnect.assert_called_once()
        
    @patch('app.utils.ibapiconnector.EClient.isConnected')
    @patch('app.utils.ibapiconnector.logger')
    def test_disconnect_without_connection(self, mock_logger, mock_is_connected):
        """Test disconnecting when not connected."""
        mock_is_connected.return_value = False
        
        # Should not raise an exception
        try:
            self.connector.close_connection()
            # Should log warning
            mock_logger.warning.assert_called()
        except Exception as e:
            self.fail(f"close_connection raised unexpected exception: {e}")
    
    # ============================================================================
    # THREAD TESTS
    # ============================================================================
    
    @patch('app.utils.ibapiconnector.EClient.connect')
    def test_thread_starts_on_connect(self, mock_connect):
        """Test that connection starts a new thread."""
        mock_connect.return_value = None
        
        self.connector.open_connection(0)
        
        self.assertIsNotNone(self.connector.connection_thread)
        self.assertIsInstance(self.connector.connection_thread, threading.Thread)
        self.assertTrue(self.connector.connection_thread.daemon)
        
    @patch('app.utils.ibapiconnector.EClient.connect')
    @patch('app.utils.ibapiconnector.EClient.run')
    def test_run_method_called_in_thread(self, mock_run, mock_connect):
        """Test that run() is called in the thread."""
        mock_connect.return_value = None
        
        self.connector.open_connection(0)
        time.sleep(0.1)  # Give thread time to start
        
        mock_run.assert_called()
    
    # ============================================================================
    # CONTEXT MANAGER TESTS
    # ============================================================================
    
    
    @patch('app.utils.ibapiconnector.EClient.connect')
    @patch('app.utils.ibapiconnector.EClient.isConnected')
    def test_context_manager_enter(self, mock_is_connected, mock_connect):
        """Test context manager __enter__ method."""
        mock_connect.return_value = None
        mock_is_connected.return_value = False
        
        with self.connector as conn:
            self.assertIs(conn, self.connector)
            mock_connect.assert_called_once()
            
    @patch('app.utils.ibapiconnector.EClient.disconnect')
    @patch('app.utils.ibapiconnector.EClient.connect')
    @patch('app.utils.ibapiconnector.EClient.isConnected')
    def test_context_manager_exit(self, mock_is_connected, mock_connect, mock_disconnect):
        """Test context manager __exit__ method."""
        mock_connect.return_value = None
        mock_is_connected.side_effect = itertools.chain([False], itertools.repeat(True))
        
        with self.connector as conn:
            pass
            
        mock_disconnect.assert_called_once()
        
    @patch('app.utils.ibapiconnector.EClient.isConnected')
    @patch('app.utils.ibapiconnector.EClient.connect')
    @patch('app.utils.ibapiconnector.EClient.disconnect')
    def test_context_manager_exception_handling(self, mock_disconnect, mock_connect, mock_is_connected):
        """Test context manager disconnects even on exception."""
        mock_connect.return_value = None
        mock_is_connected.side_effect = itertools.chain([False], itertools.repeat(True))
        
        try:
            with self.connector as conn:
                raise ValueError("Test exception")
        except ValueError:
            pass
            
        mock_disconnect.assert_called_once()
        
    @patch('app.utils.ibapiconnector.EClient.disconnect')
    @patch('app.utils.ibapiconnector.EClient.connect')
    @patch('app.utils.ibapiconnector.EClient.isConnected')
    def test_context_manager_already_connected(self, mock_is_connected, mock_connect, mock_disconnect):
        """Test context manager when already connected."""
        mock_is_connected.return_value = True  # Already connected
        
        with self.connector as conn:
            self.assertIs(conn, self.connector)
            # connect() should NOT be called since already connected
            mock_connect.assert_not_called()
        
        # But disconnect should still be called on exit
        mock_disconnect.assert_called_once()
    
    # ============================================================================
    # WRAPPER METHOD TESTS
    # ============================================================================
    
    def test_has_ewrapper_methods(self):
        """Test that connector has EWrapper methods available."""
        # Check for some common wrapper methods
        self.assertTrue(hasattr(self.connector, 'error'))
        self.assertTrue(hasattr(self.connector, 'nextValidId'))
        self.assertTrue(hasattr(self.connector, 'connectionClosed'))
        
    def test_can_override_wrapper_methods(self):
        """Test that wrapper methods can be overridden."""
        class CustomConnector(IBApiConnector):
            def __init__(self):
                super().__init__()
                self.error_called = False
                
            def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
                self.error_called = True
                
        custom = CustomConnector()
        custom.error(1, 502, "Test error")
        self.assertTrue(custom.error_called)
    
    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================
    
    @patch('app.utils.ibapiconnector.EClient.isConnected')
    @patch('app.utils.ibapiconnector.EClient.connect')
    @patch('app.utils.ibapiconnector.EClient.disconnect')
    def test_full_connection_lifecycle(self, mock_disconnect, mock_connect, mock_is_connected):
        """Test complete connection lifecycle."""
        mock_connect.return_value = None
        mock_is_connected.side_effect = itertools.chain([False], itertools.repeat(True))
               
        # Connect
        self.connector.open_connection(1)
        self.assertIsNotNone(self.connector.connection_thread)
        
        # Verify connection
        mock_connect.assert_called_once_with("localhost", 7497, 1)
        
        # Disconnect
        self.connector.close_connection()
        mock_disconnect.assert_called_once()


class TestIBApiConnectorSubclass(unittest.TestCase):
    """Test subclassing IBApiConnector."""
    
    def test_can_subclass(self):
        """Test that IBApiConnector can be subclassed."""
        class CustomService(IBApiConnector):
            def __init__(self):
                super().__init__()
                self.custom_data = []
                
        service = CustomService()
        self.assertIsInstance(service, IBApiConnector)
        self.assertIsInstance(service, EClient)
        self.assertIsInstance(service, EWrapper)
        self.assertEqual(service.custom_data, [])
        
    def test_subclass_with_wrapper_override(self):
        """Test subclass with overridden wrapper methods."""
        class CustomService(IBApiConnector):
            def __init__(self):
                super().__init__()
                self.errors = []
                
            def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
                self.errors.append({
                    'reqId': reqId,
                    'errorCode': errorCode,
                    'errorString': errorString
                })
                
        service = CustomService()
        service.error(1, 502, "Couldn't connect")
        
        self.assertEqual(len(service.errors), 1)
        self.assertEqual(service.errors[0]['errorCode'], 502)


if __name__ == '__main__':
    unittest.main()