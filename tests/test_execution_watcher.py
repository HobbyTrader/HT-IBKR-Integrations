import unittest

from app.execution_watcher import (
    EXECUTION_WATCHER_CLIENT_ID_BASE,
    EXECUTION_WATCHER_CLIENT_ID_SPAN,
    generate_execution_watcher_client_id,
)


class TestExecutionWatcherClientId(unittest.TestCase):
    def test_generated_client_id_stays_in_reserved_range(self):
        client_id = generate_execution_watcher_client_id()

        self.assertGreaterEqual(client_id, EXECUTION_WATCHER_CLIENT_ID_BASE)
        self.assertLess(client_id, EXECUTION_WATCHER_CLIENT_ID_BASE + EXECUTION_WATCHER_CLIENT_ID_SPAN)


if __name__ == "__main__":
    unittest.main()