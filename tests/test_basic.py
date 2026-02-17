import unittest
from unittest.mock import MagicMock
from datetime import datetime
from src.first_filings.core import FirstFilingAnalyzer
from src.first_filings import config

class TestFirstFilingAnalyzer(unittest.TestCase):
    def test_fetch_announcements(self):
        mock_bse = MagicMock()
        # Mock fetch_paginated_announcements return value
        mock_bse.fetch_paginated_announcements.return_value = [
            {"NEWSSUB": "Investor Presentation", "HEADLINE": "Test Headline", "SCRIP_CD": "12345"}
        ]

        analyzer = FirstFilingAnalyzer(mock_bse)
        from_date = datetime.now()
        to_date = datetime.now()

        results = analyzer.fetch_announcements(from_date, to_date)

        # Check if results contain data
        self.assertTrue(results)
        self.assertIn("PPT", results)

    def test_filter_keywords(self):
        mock_bse = MagicMock()
        analyzer = FirstFilingAnalyzer(mock_bse)

        # Test General category with keyword "Presentation"
        announcements = [
            {"NEWSSUB": "This is a Presentation", "HEADLINE": "Test"},
            {"NEWSSUB": "Just a notice", "HEADLINE": "Notice"},
        ]

        # subcat_label="PPT", subcat_value="General"
        filtered = analyzer._filter_announcements(announcements, "PPT", config.SUBCATEGORY_GENERAL)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["NEWSSUB"], "This is a Presentation")

if __name__ == '__main__':
    unittest.main()
