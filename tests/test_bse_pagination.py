import unittest
import sys
from unittest.mock import MagicMock, patch

# Mock dependencies that might be missing in the environment BEFORE importing anything
mock_bse = MagicMock()
sys.modules['bse'] = mock_bse
mock_nse = MagicMock()
sys.modules['nse'] = mock_nse

# Mock tenacity to return a pass-through decorator
def mock_retry(**kwargs):
    def decorator(func):
        return func
    return decorator

mock_tenacity = MagicMock()
mock_tenacity.retry = mock_retry
sys.modules['tenacity'] = mock_tenacity

from first_filings.bse_client import BSEClient
from first_filings import config

class TestBSEPagination(unittest.TestCase):
    def setUp(self):
        # We need to recreate the BSEClient because the class definition
        # is what gets decorated, and we want to ensure we're using our mock
        self.client = BSEClient()

    @patch('first_filings.bse_client.time.sleep', return_value=None)
    def test_pagination_limit_reached(self, mock_sleep):
        # Mock BSE announcements to always return a result but never reach total_count
        # and never return an empty list.
        mock_data = {
            "Table1": [{"ROWCNT": 10000}],
            "Table": [{"SCRIP_CD": 500001, "NEWSSUB": "Test"}]
        }
        self.client.bse.announcements = MagicMock(return_value=mock_data)

        # Set a small limit for testing
        with patch('first_filings.config.BSE_MAX_PAGES', 5):
            with self.assertLogs('first_filings.bse_client', level='WARNING') as cm:
                results = self.client.fetch_paginated_announcements(
                    from_date="2023-01-01",
                    to_date="2023-01-01",
                    category="Company Update",
                    subcategory="General"
                )

                # Check that we got 5 results (one from each page)
                self.assertEqual(len(results), 5)
                # Check that the warning was logged
                self.assertTrue(any("Reached maximum pages (5)" in output for output in cm.output))
                # Check that it called exactly 5 times
                self.assertEqual(self.client.bse.announcements.call_count, 5)

    @patch('first_filings.bse_client.time.sleep', return_value=None)
    def test_pagination_stops_normally(self, mock_sleep):
        # Mock BSE announcements to return 2 pages and then stop
        def mock_announcements(page_no, **kwargs):
            if page_no == 1:
                return {
                    "Table1": [{"ROWCNT": 2}],
                    "Table": [{"SCRIP_CD": 500001, "NEWSSUB": "Test 1"}]
                }
            elif page_no == 2:
                return {
                    "Table1": [{"ROWCNT": 2}],
                    "Table": [{"SCRIP_CD": 500002, "NEWSSUB": "Test 2"}]
                }
            else:
                return {"Table1": [{"ROWCNT": 2}], "Table": []}

        self.client.bse.announcements = MagicMock(side_effect=mock_announcements)

        results = self.client.fetch_paginated_announcements(
            from_date="2023-01-01",
            to_date="2023-01-01",
            category="Company Update",
            subcategory="General"
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(self.client.bse.announcements.call_count, 2)

if __name__ == '__main__':
    unittest.main()
