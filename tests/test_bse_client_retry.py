import unittest
from unittest.mock import MagicMock, patch
from first_filings.bse_client import BSEClient, should_retry

class TestBSEClientRetry(unittest.TestCase):

    def test_should_retry_timeout(self):
        self.assertTrue(should_retry(TimeoutError("Timeout")))

    def test_should_retry_connection_error_429(self):
        self.assertTrue(should_retry(ConnectionError("429: Too Many Requests")))

    def test_should_retry_connection_error_500(self):
        self.assertTrue(should_retry(ConnectionError("500: Server Error")))

    def test_should_retry_connection_error_502(self):
        self.assertTrue(should_retry(ConnectionError("502: Bad Gateway")))

    def test_should_not_retry_connection_error_404(self):
        self.assertFalse(should_retry(ConnectionError("404: Not Found")))

    def test_should_not_retry_connection_error_400(self):
        self.assertFalse(should_retry(ConnectionError("400: Bad Request")))

    def test_should_retry_other_connection_error(self):
        self.assertTrue(should_retry(ConnectionError("Connection Refused")))

    def test_should_retry_value_error(self):
        self.assertTrue(should_retry(ValueError("Some Value Error")))

    @patch("first_filings.bse_client.BSE")
    def test_fetch_paginated_announcements_retries(self, mock_bse_class):
        # Setup mock
        mock_bse_instance = MagicMock()
        mock_bse_class.return_value = mock_bse_instance

        # Mock bse.announcements to fail 2 times then succeed
        mock_bse_instance.announcements.side_effect = [
            TimeoutError("Timeout"),
            ConnectionError("500: Server Error"),
            {"Table": [{"SCRIP_CD": "12345"}], "Table1": [{"ROWCNT": 1}]}
        ]

        client = BSEClient()

        # Mock time.sleep to speed up tests
        with patch("tenacity.nap.time.sleep"):
            result = client.fetch_paginated_announcements(
                from_date="2023-01-01",
                to_date="2023-01-01",
                category="Cat",
                subcategory="SubCat"
            )

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["SCRIP_CD"], "12345")
            self.assertEqual(mock_bse_instance.announcements.call_count, 3)

    @patch("first_filings.bse_client.BSE")
    def test_fetch_paginated_announcements_stops_on_404(self, mock_bse_class):
        mock_bse_instance = MagicMock()
        mock_bse_class.return_value = mock_bse_instance

        # Mock bse.announcements to fail with 404
        mock_bse_instance.announcements.side_effect = ConnectionError("404: Not Found")

        client = BSEClient()

        with self.assertRaises(ConnectionError):
            client.fetch_paginated_announcements(
                from_date="2023-01-01",
                to_date="2023-01-01",
                category="Cat",
                subcategory="SubCat"
            )

        # Should only call once because 404 is not retried
        self.assertEqual(mock_bse_instance.announcements.call_count, 1)

if __name__ == '__main__':
    unittest.main()
