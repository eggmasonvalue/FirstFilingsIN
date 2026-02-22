import argparse
import os
import sys
import json
import requests

MAX_EMBEDS_PER_MESSAGE = 10
MAX_FIELD_VALUE = 1000

def send_embeds(webhook_url, embeds):
    """Send a list of embeds to Discord, chunking if necessary."""
    for i in range(0, len(embeds), MAX_EMBEDS_PER_MESSAGE):
        chunk = embeds[i:i + MAX_EMBEDS_PER_MESSAGE]
        payload = {"embeds": chunk}
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code not in [200, 204]:
                print(f"Failed to send embeds chunk {i}. Status: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Error sending embeds: {e}")

def format_filing(filing):
    # filing: [scrip_code, company_name, price_at_announcement, current_price, current_mkt_cap_cr]
    symbol = filing[0]
    name = filing[1]
    price_at = filing[2]
    curr_price = filing[3]
    mkt_cap = filing[4]

    # Format numbers
    def fmt_price(p):
        if p is None: return "N/A"
        return f"₹{p:,.2f}" if isinstance(p, (int, float)) else str(p)

    mkt_cap_str = f"₹{mkt_cap} Cr" if mkt_cap is not None else "N/A"

    return f"**{name}** ({symbol})\nPrice: {fmt_price(price_at)} -> {fmt_price(curr_price)} | MCap: {mkt_cap_str}\n\n"

def process_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    filings_data = data.get("data", {})
    if not filings_data:
        print("No data found in file.")
        return []

    embeds = []

    # Iterate over categories
    for category, dates_dict in filings_data.items():
        # Iterate over dates
        for date_str, filings_list in dates_dict.items():
            if not filings_list:
                continue

            current_embed = {
                "title": f"{category} - {date_str}",
                "color": 3447003, # Blueish
                "fields": []
            }

            current_field_value = ""

            for filing in filings_list:
                text = format_filing(filing)

                # Check limits
                if len(current_field_value) + len(text) > MAX_FIELD_VALUE:
                    # Flush field
                    current_embed["fields"].append({
                        "name": "Filings",
                        "value": current_field_value,
                        "inline": False
                    })
                    current_field_value = text

                    # Check embed size limits (fields count limit is 25)
                    if len(current_embed["fields"]) >= 25:
                        embeds.append(current_embed)
                        current_embed = {
                            "title": f"{category} - {date_str} (cont.)",
                            "color": 3447003,
                            "fields": []
                        }
                else:
                    current_field_value += text

            # Flush remaining field
            if current_field_value:
                 current_embed["fields"].append({
                        "name": "Filings",
                        "value": current_field_value,
                        "inline": False
                    })

            embeds.append(current_embed)

    return embeds

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send JSON output to Discord as Embeds.")
    parser.add_argument("file_path", help="Path to the JSON output file.")

    args = parser.parse_args()

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL environment variable not set.")
        sys.exit(0)

    if not os.path.exists(args.file_path):
        print(f"File not found: {args.file_path}")
        sys.exit(1)

    try:
        embeds = process_file(args.file_path)
        if embeds:
            send_embeds(webhook_url, embeds)
            print(f"Sent {len(embeds)} embeds to Discord.")
        else:
            print("No filings to send.")

    except Exception as e:
        print(f"Error processing/sending: {e}")
        sys.exit(1)
