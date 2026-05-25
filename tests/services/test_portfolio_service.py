import unittest
from unittest.mock import Mock, patch

from app.services.portfolio import PortfolioService


class TestPortfolioServiceCallbacks(unittest.TestCase):
    def setUp(self):
        self.service = PortfolioService()

    def test_update_portfolio_stores_snapshot(self):
        contract = Mock()
        contract.conId = 123
        contract.symbol = "AAPL"

        self.service.updatePortfolio(
            contract,
            12,
            150.5,
            1806.0,
            140.0,
            12.5,
            4.0,
            "DU123456",
        )

        self.assertEqual(len(self.service.portfolio_updates), 1)
        self.assertEqual(self.service.portfolio_updates[0]["account_name"], "DU123456")

    def test_account_summary_stores_snapshot_and_end_event(self):
        self.service.accountSummary(7, "DU123456", "NetLiquidation", "100000", "USD")
        self.assertEqual(len(self.service.account_summaries), 1)
        self.assertEqual(self.service.account_summaries[0]["req_id"], 7)

        self.service.accountSummaryEnd(7)
        self.assertTrue(self.service._get_event("account_summary_end_7").is_set())

    def test_position_callbacks_store_snapshot_and_end_event(self):
        contract = Mock()
        contract.conId = 555
        contract.symbol = "MSFT"

        self.service.position("DU123456", contract, 5.0, 320.0)
        self.assertEqual(len(self.service.open_positions), 1)

        self.service.positionEnd()
        self.assertTrue(self.service._get_event("position_end").is_set())

    @patch("app.services.portfolio.PortfolioService.reqAccountUpdates")
    @patch("app.services.portfolio.PortfolioService.reqAccountSummary")
    @patch("app.services.portfolio.PortfolioService.reqPositions")
    @patch("app.services.portfolio.PortfolioService.cancelAccountSummary")
    @patch("app.services.portfolio.PortfolioService.cancelPositions")
    def test_collect_portfolio_snapshot_requests_portfolio_data(
        self,
        mock_cancel_positions,
        mock_cancel_account_summary,
        mock_req_positions,
        mock_req_account_summary,
        mock_req_account_updates,
    ):
        self.service._get_event("account_download_end").set()
        self.service._get_event("position_end").set()

        with patch.object(self.service, "_wait_for_event", return_value=True):
            snapshot = self.service.collect_portfolio_snapshot(account_id="DU123456")

        self.assertIn("portfolio_updates", snapshot)
        mock_req_account_updates.assert_any_call(True, "DU123456")
        mock_req_positions.assert_called_once()
        mock_req_account_summary.assert_called_once()
        mock_cancel_positions.assert_called_once()
        mock_cancel_account_summary.assert_called_once()


if __name__ == "__main__":
    unittest.main()