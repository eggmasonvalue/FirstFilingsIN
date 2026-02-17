import json
import logging
import os
from datetime import datetime
from . import config

def setup_logging(log_file=config.LOG_FILE):
    """
    Configure logging to write to a file.
    Overwrites the log file on each run.
    """
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        filename=log_file,
        filemode='w',  # Overwrite mode
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Redirect stdout and stderr to logging if needed,
    # but cleaner is to just use logging everywhere and avoid print().
    # However, if libraries use print, we might want to capture it.
    # For now, we will rely on using logging module.

def archive_output(output_data, archive_file=config.ARCHIVE_FILE):
    """
    Append the output data to the archive file.
    """
    archive_data = []
    if os.path.exists(archive_file):
        try:
            with open(archive_file, 'r') as f:
                content = f.read()
                if content:
                    archive_data = json.loads(content)
                    if not isinstance(archive_data, list):
                        archive_data = [archive_data]
        except json.JSONDecodeError:
            logging.error(f"Failed to decode archive file {archive_file}. Starting new archive.")
        except Exception as e:
            logging.error(f"Error reading archive file: {e}")

    # Add timestamp to the record if not present
    if isinstance(output_data, dict) and "archived_at" not in output_data:
        output_data["archived_at"] = datetime.now().isoformat()

    archive_data.append(output_data)

    try:
        with open(archive_file, 'w') as f:
            json.dump(archive_data, f, indent=2)
        logging.info(f"Output archived to {archive_file}")
    except Exception as e:
        logging.error(f"Failed to write to archive file: {e}")

def print_json_output(data):
    """
    Print the data as JSON to stdout.
    """
    print(json.dumps(data, indent=2))
