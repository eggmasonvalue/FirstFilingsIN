import unittest
from unittest.mock import MagicMock
from datetime import datetime
from first_filings.core import FirstFilingAnalyzer
from first_filings.exchange import Announcement

class TestFirstFilingAnalyzer(unittest.TestCase):
    def test_fetch_announcements(self):
        mock_client = MagicMock()
        # Mock fetch_announcements return value
        mock_announcement = Announcement(
            scrip_code="12345",
            company_name="Test Corp",
            date=datetime.now(),
            category="PPT",
            description="Investor Presentation"
        )
        mock_client.fetch_announcements.return_value = [mock_announcement]

        analyzer = FirstFilingAnalyzer(mock_client)
        from_date = datetime.now()
        to_date = datetime.now()

        # Test specific category
        results = analyzer.fetch_announcements(from_date, to_date, categories=["PPT"])

        self.assertTrue(results)
        self.assertIn("PPT", results)
        self.assertEqual(len(results["PPT"]), 1)
        self.assertEqual(results["PPT"][0], mock_announcement)

        # Verify client was called correctly
        mock_client.fetch_announcements.assert_called_with(
            from_date=from_date,
            to_date=to_date,
            category="PPT"
        )

    def test_is_first_filing_true(self):
        mock_client = MagicMock()
        analyzer = FirstFilingAnalyzer(mock_client)

        # Scenario: Only 1 filing found in history (the current one)
        mock_client.fetch_announcements.return_value = [MagicMock()]

        result = analyzer.is_first_filing(
            scrip_code="12345",
            category_label="PPT",
            filing_date=datetime.now(),
            lookback_years=2,
            company_name="Test Corp"
        )

        self.assertTrue(result)

    def test_is_first_filing_false(self):
        mock_client = MagicMock()
        analyzer = FirstFilingAnalyzer(mock_client)

        # Scenario: 2 filings found (current one + previous one)
        mock_client.fetch_announcements.return_value = [MagicMock(), MagicMock()]

        result = analyzer.is_first_filing(
            scrip_code="12345",
            category_label="PPT",
            filing_date=datetime.now(),
            lookback_years=2,
            company_name="Test Corp"
        )

        self.assertFalse(result)

    def test_enrich_filing_data(self):
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
            announcement_date_str=datetime.now()
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["scrip_code"], "12345")
        self.assertEqual(result["company_name"], "Test Corp")
        self.assertEqual(result["current_price"], 100.0)
        self.assertEqual(result["current_mkt_cap_cr"], 10)
        self.assertEqual(result["price_at_announcement"], 90.0)

if __name__ == '__main__':
    unittest.main()
