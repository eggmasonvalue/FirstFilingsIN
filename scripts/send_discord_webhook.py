import argparse
import os
import sys
import requests
import json

def send_file_to_discord(webhook_url, file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    # Check file size (Discord free tier limit is 8MB generally, sometimes 25MB)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > 25:
        print(f"Warning: File size ({file_size_mb:.2f}MB) exceeds Discord upload limits (25MB). Attempting anyway.")

    try:
        with open(file_path, 'rb') as f:
            filename = os.path.basename(file_path)
            # Discord webhook payload for file upload
            files = {
                'file': (filename, f)
            }
            # Optional: Add a message content
            payload = {
                'content': f"Here is the daily report for **{filename}**"
            }

            response = requests.post(webhook_url, data=payload, files=files)

            if response.status_code in [200, 204]:
                print(f"Successfully sent {filename} to Discord.")
            else:
                print(f"Failed to send {filename}. Status: {response.status_code}")
                print(f"Response: {response.text}")
                sys.exit(1)

    except Exception as e:
        print(f"Error sending file to Discord: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a file to Discord via Webhook.")
    parser.add_argument("file_path", help="Path to the file to send.")

    args = parser.parse_args()

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL environment variable not set. Skipping Discord notification.")
        # We don't exit with error here because we don't want to fail the CI job if the secret is missing,
        # just skip the notification.
        sys.exit(0)

    send_file_to_discord(webhook_url, args.file_path)
