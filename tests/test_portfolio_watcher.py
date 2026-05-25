import unittest

from app.portfolio_watcher import (
    PORTFOLIO_WATCHER_CLIENT_ID_BASE,
    PORTFOLIO_WATCHER_CLIENT_ID_SPAN,
    generate_portfolio_watcher_client_id,
)


class TestPortfolioWatcherClientId(unittest.TestCase):
    def test_generated_client_id_stays_in_reserved_range(self):
        client_id = generate_portfolio_watcher_client_id("DU123456")

        self.assertGreaterEqual(client_id, PORTFOLIO_WATCHER_CLIENT_ID_BASE)
        self.assertLess(client_id, PORTFOLIO_WATCHER_CLIENT_ID_BASE + PORTFOLIO_WATCHER_CLIENT_ID_SPAN)


if __name__ == "__main__":
    unittest.main()