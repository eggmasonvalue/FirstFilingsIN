import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from first_filings.core import FirstFilingAnalyzer
from first_filings.bse_client import BSEClient
from first_filings.nse_client import NSEClient

class TestEnrichment(unittest.TestCase):
    def test_enrich_filing_data_attachment(self):
        mock_client = MagicMock()
        analyzer = FirstFilingAnalyzer(mock_client)

        # Mock get_scrip_info
        mock_client.get_scrip_info.return_value = {
            "symbol": "TEST",
            "company_name": "Test Corp",
            "current_price": 100.0,
            "price_at_announcement": 90.0,
            "current_mkt_cap_cr": 10
        }

        result = analyzer.enrich_filing_data(
            scrip_code="12345",
            announcement_date_str=datetime.now(),
            attachment_url="http://example.com/file.pdf"
        )

        self.assertEqual(result["attachment_url"], "http://example.com/file.pdf")

    @patch('first_filings.bse_client.BSE')
    def test_bse_lookback(self, MockBSE):
        client = BSEClient()
        # client.bse is the mock instance
        mock_bse_instance = client.bse

        # Mock lookup/quote/trading to avoid noise
        mock_bse_instance.lookup.return_value = {"symbol": "TEST", "company_name": "Test Co"}
        mock_bse_instance.quote.return_value = {"LTP": 100}

        # Mock historical data: Only has data for 2 days ago
        today = datetime.now()
        two_days_ago = today - timedelta(days=2)
        # Format: 'Thu Feb 20 2025 00:00:00'
        # %a %b %d %Y %H:%M:%S
        # Wait, datetime default str matches this roughly? No.
        target_date_str = two_days_ago.strftime("%a %b %d %Y %H:%M:%S")

        # Make sure the str format matches what the code expects
        # The code uses: datetime.strptime(d_str, "%a %b %d %Y %H:%M:%S")

        mock_bse_instance.equityPriceVolumeT12M.return_value = {
            "Data": {
                "data": [
                    [target_date_str, "95.0", "1000"]
                ]
            }
        }

        # Call with today's date (missing in history)
        info = client.get_scrip_info("500000", today)

        # Should pick up the price from 2 days ago
        self.assertEqual(info["price_at_announcement"], 95.0)

    @patch('first_filings.nse_client.NSE')
    def test_nse_lookback_and_series(self, MockNSE):
        client = NSEClient()
        mock_nse_instance = client.nse

        # Mock quote with activeSeries='BE'
        mock_nse_instance.quote.return_value = {
            "info": {
                "companyName": "Test Co",
                "activeSeries": ["BE"]
            },
            "priceInfo": {"lastPrice": 100},
            "securityInfo": {"issuedSize": 10000000}
        }

        # Mock historical data
        mock_nse_instance.fetch_equity_historical_data.return_value = [
            {"chClosingPrice": 90.0, "mtimestamp": "20-Feb-2026"}
        ]

        today = datetime.now()
        info = client.get_scrip_info("TEST", today)

        # Verify series='BE' was passed
        # Check call args
        args, kwargs = mock_nse_instance.fetch_equity_historical_data.call_args
        self.assertEqual(kwargs.get('series'), 'BE')

        # Verify price
        self.assertEqual(info["price_at_announcement"], 90.0)

if __name__ == '__main__':
    unittest.main()
