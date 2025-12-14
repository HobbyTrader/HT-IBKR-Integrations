import threading
import logging

logger = logging.getLogger(__name__)

class OrderCoordinator:
    def __init__(self):
        self.pending_events = []  # Track all order Events
        self.lock = threading.Lock()
        self.client_id_counter = 0
        self.client_id_lock = threading.Lock()
        
    def add_event(self, event):
        with self.lock:
            self.pending_events.append(event)
    
    def get_next_clientId(self):
        with self.client_id_lock:
            self.client_id_counter += 1
            return self.client_id_counter
            
    async def wait_all_orders(self, timeout_per_order=30.0):
        """Wait for ALL orders across ALL services to complete."""
        logger.info(f"Waiting for {len(self.pending_events)} orders...")
        
        for event in self.pending_events:
            success = event.wait(timeout=timeout_per_order)
            if not success:
                logger.error("Order timeout!")
                # Continue or raise based on your needs
                
        logger.info("ALL orders completed!")
        self.pending_events.clear()