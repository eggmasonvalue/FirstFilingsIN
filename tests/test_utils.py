import unittest
from unittest.mock import patch, mock_open, MagicMock
from first_filings.utils import save_output, setup_logging

class TestUtils(unittest.TestCase):
    def test_setup_logging_dir_creation(self):
        log_file = "logs/test.log"
        with patch("os.path.exists", return_value=False) as mock_exists:
            with patch("os.makedirs") as mock_makedirs:
                with patch("logging.basicConfig") as mock_basic_config:
                    with patch("logging.root.removeHandler") as mock_remove_handler:
                        # Mock logging.root.handlers as a list
                        with patch("logging.root.handlers", [MagicMock()]):
                            setup_logging(log_file)

                            mock_exists.assert_called_once_with("logs")
                            mock_makedirs.assert_called_once_with("logs")
                            mock_remove_handler.assert_called()
                            mock_basic_config.assert_called_once()
                            _, kwargs = mock_basic_config.call_args
                            self.assertEqual(kwargs['filename'], log_file)
                            self.assertEqual(kwargs['filemode'], 'w')

    def test_setup_logging_no_dir(self):
        # Case where log_file is just a filename in current directory
        log_file = "test.log"
        with patch("os.path.exists") as mock_exists:
            with patch("os.makedirs") as mock_makedirs:
                with patch("logging.basicConfig"):
                    setup_logging(log_file)
                    mock_exists.assert_not_called()
                    mock_makedirs.assert_not_called()

    def test_setup_logging_dir_exists(self):
        log_file = "logs/test.log"
        with patch("os.path.exists", return_value=True) as mock_exists:
            with patch("os.makedirs") as mock_makedirs:
                with patch("logging.basicConfig"):
                    setup_logging(log_file)
                    mock_exists.assert_called_once_with("logs")
                    mock_makedirs.assert_not_called()

    def test_save_output_success(self):
        # Sample input data
        filings_data = {
            "PPT": [
                {
                    "scrip_code": "500010",
                    "company_name": "HDFC",
                    "date": "2023-05-01",
                    "price_at_announcement": 2400.0,
                    "current_price": 2500.0,
                    "current_mkt_cap_cr": 450000.0,
                    "attachment_url": "http://example.com/ppt",
                    "financial_snapshot": "Net Profit: 100cr"
                }
            ]
        }
        failed_checks_count = 5
        lookback_years = 2
        filename = "test_output.json"

        # Mock datetime to have a fixed value for generated_at
        fixed_now_str = "2023-10-27T12:00:00"

        with patch("first_filings.utils.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = fixed_now_str

            with patch("builtins.open", mock_open()):
                with patch("json.dump") as mock_json_dump:
                    result = save_output(filings_data, failed_checks_count, lookback_years, filename)

                    self.assertEqual(result, filename)

                    # Verify the data passed to json.dump
                    # It should be the first argument
                    args, kwargs = mock_json_dump.call_args
                    output_data = args[0]

                    self.assertEqual(output_data["meta"]["failed_checks_count"], failed_checks_count)
                    self.assertEqual(output_data["meta"]["lookback_years"], lookback_years)
                    self.assertEqual(output_data["meta"]["generated_at"], fixed_now_str)

                    # Verify transformation
                    expected_row = [
                        "500010",
                        "HDFC",
                        2400.0,
                        2500.0,
                        450000.0,
                        "http://example.com/ppt",
                        "Net Profit: 100cr"
                    ]
                    self.assertEqual(output_data["data"]["PPT"]["2023-05-01"], [expected_row])

    def test_save_output_failure(self):
        filings_data = {"PPT": []}
        failed_checks_count = 0
        lookback_years = 2
        filename = "test_output.json"

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch("logging.error") as mock_log_error:
                result = save_output(filings_data, failed_checks_count, lookback_years, filename)

                self.assertIsNone(result)
                mock_log_error.assert_called_once()
                # Verify it logged the error message with the exception
                args, _ = mock_log_error.call_args
                self.assertIn("Failed to save output file", args[0])
                self.assertIn("Permission denied", args[0])

if __name__ == "__main__":
    unittest.main()
