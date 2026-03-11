import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import sys

# Mock tenacity and nse BEFORE importing anything from first_filings
sys.modules['tenacity'] = MagicMock()
# Mock the decorator
def mock_retry(f):
    return f
sys.modules['tenacity'].retry = lambda *args, **kwargs: mock_retry

# Also need to mock others used in retries.py if it gets imported
sys.modules['tenacity'].wait_random_exponential = MagicMock()
sys.modules['tenacity'].stop_after_attempt = MagicMock()
sys.modules['tenacity'].retry_if_exception = MagicMock()
sys.modules['tenacity'].before_sleep_log = MagicMock()

mock_nse_lib = MagicMock()
sys.modules['nse'] = mock_nse_lib

# Now import
from first_filings.nse_client import NSEClient

class TestNSEClientDateParsing(unittest.TestCase):
    def setUp(self):
        self.client = NSEClient()
        self.client.nse = MagicMock()

    @patch('first_filings.nse_client.config')
    def test_fetch_announcements_date_parsing_an_dt(self, mock_config):
        mock_config.NSE_CATEGORY_KEYWORDS.get.return_value = ["Press Release"]

        # Case 1: an_dt in %d-%b-%Y %H:%M:%S format
        expected_date = datetime(2023, 10, 27, 10, 30, 0)
        self.client.nse.announcements.return_value = [
            {
                "symbol": "TEST",
                "desc": "Press Release about something",
                "an_dt": "27-Oct-2023 10:30:00",
                "attchmntFile": "http://example.com/file.pdf"
            }
        ]

        results = self.client.fetch_announcements(
            datetime.now(), datetime.now(), category="Other", subcategory="Press Release"
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].date, expected_date)

    @patch('first_filings.nse_client.config')
    def test_fetch_announcements_date_parsing_sort_date_fallback(self, mock_config):
        mock_config.NSE_CATEGORY_KEYWORDS.get.return_value = ["Press Release"]

        # Case 2: an_dt malformed, sort_date in %Y-%m-%d %H:%M:%S format
        expected_date = datetime(2023, 10, 27, 10, 30, 0)
        self.client.nse.announcements.return_value = [
            {
                "symbol": "TEST",
                "desc": "Press Release about something",
                "an_dt": "invalid-date",
                "sort_date": "2023-10-27 10:30:00"
            }
        ]

        results = self.client.fetch_announcements(
            datetime.now(), datetime.now(), category="Other", subcategory="Press Release"
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].date, expected_date)

    @patch('first_filings.nse_client.config')
    def test_fetch_announcements_date_parsing_missing_an_dt(self, mock_config):
        mock_config.NSE_CATEGORY_KEYWORDS.get.return_value = ["Press Release"]

        # Case 3: an_dt missing
        self.client.nse.announcements.return_value = [
            {
                "symbol": "TEST",
                "desc": "Press Release about something"
            }
        ]

        # Use patch to mock datetime.now() to return a fixed value
        fixed_now = datetime(2023, 1, 1, 12, 0, 0)
        with patch('first_filings.nse_client.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            # Also need to mock strptime since it's also called from datetime
            mock_datetime.strptime.side_effect = datetime.strptime

            results = self.client.fetch_announcements(
                datetime.now(), datetime.now(), category="Other", subcategory="Press Release"
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].date, fixed_now)

    @patch('first_filings.nse_client.config')
    def test_fetch_announcements_date_parsing_missing_an_dt_but_sort_date_present(self, mock_config):
        mock_config.NSE_CATEGORY_KEYWORDS.get.return_value = ["Press Release"]

        # Case 5: an_dt missing, but sort_date present
        expected_date = datetime(2023, 10, 27, 10, 30, 0)
        self.client.nse.announcements.return_value = [
            {
                "symbol": "TEST",
                "desc": "Press Release about something",
                "sort_date": "2023-10-27 10:30:00"
            }
        ]

        results = self.client.fetch_announcements(
            datetime.now(), datetime.now(), category="Other", subcategory="Press Release"
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].date, expected_date)

    @patch('first_filings.nse_client.config')
    def test_fetch_announcements_date_parsing_all_malformed(self, mock_config):
        mock_config.NSE_CATEGORY_KEYWORDS.get.return_value = ["Press Release"]

        # Case 4: Both an_dt and sort_date malformed
        self.client.nse.announcements.return_value = [
            {
                "symbol": "TEST",
                "desc": "Press Release about something",
                "an_dt": "invalid",
                "sort_date": "also-invalid"
            }
        ]

        fixed_now = datetime(2023, 1, 1, 12, 0, 0)
        with patch('first_filings.nse_client.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            mock_datetime.strptime.side_effect = datetime.strptime

            results = self.client.fetch_announcements(
                datetime.now(), datetime.now(), category="Other", subcategory="Press Release"
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].date, fixed_now)

if __name__ == '__main__':
    unittest.main()
