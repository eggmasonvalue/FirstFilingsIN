import unittest
from unittest.mock import MagicMock, patch
from src.first_filings.retries import should_retry_exception, retry_exchange
from src.first_filings.nse_client import NSEClient
from src.first_filings.bse_client import BSEClient
from datetime import datetime

class TestRetries(unittest.TestCase):

    def test_should_retry_predicate(self):
        # Retryable exceptions
        self.assertTrue(should_retry_exception(TimeoutError("Client timeout")))
        self.assertTrue(should_retry_exception(ConnectionError("503 Service Unavailable")))
        self.assertTrue(should_retry_exception(ConnectionError("Error 503: Service Unavailable")))
        self.assertTrue(should_retry_exception(ConnectionError("429 Too Many Requests")))
        self.assertTrue(should_retry_exception(ConnectionError("502 Bad Gateway")))
        self.assertTrue(should_retry_exception(ConnectionError("504 Gateway Timeout")))
        self.assertTrue(should_retry_exception(ConnectionError("408 Request Timeout")))

        # NSE format
        self.assertTrue(should_retry_exception(ConnectionError("https://nseindia.com/api 503: Service Unavailable")))

        # Non-retryable exceptions
        self.assertFalse(should_retry_exception(ConnectionError("404 Not Found")))
        self.assertFalse(should_retry_exception(ConnectionError("500 Internal Server Error")))
        self.assertFalse(should_retry_exception(ConnectionError("403 Forbidden")))
        self.assertFalse(should_retry_exception(ConnectionError("Connection refused"))) # Generic network error
        self.assertFalse(should_retry_exception(ValueError("Some value error")))
        self.assertFalse(should_retry_exception(Exception("Generic exception")))

    def test_nse_client_methods_are_decorated(self):
        # Check if methods are decorated by inspecting if they have tenacity attributes
        # Or by mocking the underlying call and seeing if it retries.

        client = NSEClient()
        # Mock the underlying nse object
        client.nse = MagicMock()

        # Mock nse.announcements to fail twice then succeed
        client.nse.announcements.side_effect = [
            ConnectionError("503 Service Unavailable"),
            ConnectionError("502 Bad Gateway"),
            [{"symbol": "TEST", "desc": "Press Release about something"}]
        ]

        # Patch time.sleep to avoid waiting
        with patch('time.sleep'):
            from_date = datetime.now()
            to_date = datetime.now()

            # Use a category that exists in config or mock config
            result = client.fetch_announcements(from_date, to_date, "Press Release")

            self.assertEqual(len(result), 1)
            self.assertEqual(client.nse.announcements.call_count, 3)

    def test_bse_client_methods_are_decorated(self):
        client = BSEClient()
        client.bse = MagicMock()

        # Mock bse.announcements to fail once then succeed
        client.bse.announcements.side_effect = [
            TimeoutError("Timeout"),
            {"Table": [{"SCRIP_CD": "12345", "NEWSSUB": "Test"}], "Table1": [{"ROWCNT": 1}]}
        ]

        with patch('time.sleep'):
            from_date = datetime.now()
            to_date = datetime.now()

            # fetch_paginated_announcements is called by fetch_announcements
            # But fetch_paginated_announcements is the decorated one.
            # We can test fetch_paginated_announcements directly.

            result = client.fetch_paginated_announcements(from_date, to_date, "Cat", "SubCat")

            self.assertTrue(result)
            self.assertEqual(client.bse.announcements.call_count, 2)

    def test_non_retryable_error_propagates(self):
        client = NSEClient()
        client.nse = MagicMock()
        client.nse.announcements.side_effect = ConnectionError("404 Not Found")

        with patch('time.sleep'):
            with self.assertRaises(ConnectionError):
                 client.fetch_announcements(datetime.now(), datetime.now(), "Category")

            # Should only call once
            self.assertEqual(client.nse.announcements.call_count, 1)

if __name__ == '__main__':
    unittest.main()
