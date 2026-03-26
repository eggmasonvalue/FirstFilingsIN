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
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code not in [200, 204]:
                print(f"Failed to send embeds chunk {i}. Status: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Error sending embeds: {e}")

def format_filing(filing):
    # filing: [scrip_code, company_name, price_at_announcement, current_price, current_mkt_cap_cr, attachment_url, financial_snapshot]
    symbol = filing[0]
    name = filing[1]
    price_at = filing[2]
    curr_price = filing[3]
    mkt_cap = filing[4]

    # Handle optional attachment_url (index 5)
    attachment_url = filing[5] if len(filing) > 5 else None

    # Handle optional financial_snapshot (index 6)
    financial_snapshot = filing[6] if len(filing) > 6 else None

    # Format numbers
    def fmt_price(p):
        if p is None:
            return "N/A"
        return f"₹{p:,.2f}" if isinstance(p, (int, float)) else str(p)

    mkt_cap_str = f"₹{mkt_cap} Cr" if mkt_cap is not None else "N/A"

    # Calculate percentage change if prices are available
    pct_change_str = ""
    if isinstance(price_at, (int, float)) and isinstance(curr_price, (int, float)) and price_at > 0:
        change = ((curr_price - price_at) / price_at) * 100
        sign = "+" if change > 0 else ""
        pct_change_str = f" ({sign}{change:.1f}%)"

    # Construct Title with Link
    title = f"**{name}**"
    if attachment_url:
        title = f"[{name}]({attachment_url})"

    # Financial Snapshot Formatting
    fin_str = ""
    if financial_snapshot and isinstance(financial_snapshot, dict):
        # Expecting structure from resultsSnapshot['results_in_crores']:
        # { "fields": ["title", "Dec-25", "Sep-25", "FY24-25"], "data": [ ["Revenue", ...], ... ] }

        fields = financial_snapshot.get("fields", [])
        data_rows = financial_snapshot.get("data", [])

        if fields and data_rows:
            # Construct a Markdown table in a code block
            # We will show the first 3 columns: Title, Latest Quarter, Previous Quarter
            # (Assuming fields[0] is title, fields[1] is latest)

            # Determine headers to show (limit width for Discord)
            # Typically fields: ["title", "Dec-25", "Sep-25", "FY..."]
            headers = fields

            # Calculate column widths
            col_widths = [len(h) for h in headers]

            # Pre-process rows to limit to same columns and update widths
            rows_to_show = []
            for row in data_rows:
                # row is e.g. ["Revenue", "123", "456", "789"]
                sliced_row = row
                rows_to_show.append(sliced_row)
                for i, val in enumerate(sliced_row):
                    if i < len(col_widths):
                        col_widths[i] = max(col_widths[i], len(str(val)))

            # Build Table String
            # Header
            header_line = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
            separator_line = "-+-".join("-" * w for w in col_widths)

            table_lines = [header_line, separator_line]

            for row in rows_to_show:
                row_line = " | ".join(f"{str(val):<{col_widths[i]}}" for i, val in enumerate(row))
                table_lines.append(row_line)

            table_content = "\n".join(table_lines)
            fin_str = f"\n```\n{table_content}\n```"

    return f"- {title} ({symbol})\n  **Price:** {fmt_price(price_at)} -> {fmt_price(curr_price)}{pct_change_str} | **MCap:** {mkt_cap_str}{fin_str}\n\n"

def process_file(file_path, exchange_name):
    with open(file_path, 'r') as f:
        data = json.load(f)

    filings_data = data.get("data", {})
    if not filings_data:
        print("No data found in file.")
        return []

    embeds = []

    # Structure: One or more embeds starting with Exchange Name
    # H1: Exchange (Title of Embed)
    # H2: Category (## Category)
    # H3: Date (### Date)

    current_embed = {
        "title": f"{exchange_name}",
        "color": 3447003, # Blueish
    }
    current_description = ""

    # Sort categories to ensure consistent order
    sorted_categories = sorted(filings_data.keys())

    for category in sorted_categories:
        dates_dict = filings_data[category]
        if not dates_dict:
            continue

        # Add Category Header
        cat_header = f"## {category}\n"

        # Check limits for Category Header
        if len(current_description) + len(cat_header) > 4000:
             current_embed["description"] = current_description
             embeds.append(current_embed)
             current_embed = {
                "title": f"{exchange_name} (cont.)",
                "color": 3447003,
             }
             current_description = ""

        current_description += cat_header

        # Sort dates
        sorted_dates = sorted(dates_dict.keys())

        for date_str in sorted_dates:
            filings_list = dates_dict[date_str]
            if not filings_list:
                continue

            # Add Date Header
            date_header = f"### {date_str}\n"

            # Check limits for Date Header
            if len(current_description) + len(date_header) > 4000:
                 current_embed["description"] = current_description
                 embeds.append(current_embed)
                 current_embed = {
                    "title": f"{exchange_name} (cont.)",
                    "color": 3447003,
                 }
                 # If we split here, we might want to re-add Category header for context?
                 # Ideally yes, but let's keep it simple first or stick to strict hierarchy.
                 # Re-adding category header if split happens:
                 current_description = f"## {category} (cont.)\n"

            current_description += date_header

            for filing in filings_list:
                text = format_filing(filing)

                # Check limits for Content
                if len(current_description) + len(text) > 4000:
                    # Flush current embed
                    current_embed["description"] = current_description
                    embeds.append(current_embed)

                    # Start new embed
                    current_embed = {
                        "title": f"{exchange_name} (cont.)",
                        "color": 3447003,
                    }
                    # Context restoration: Exchange -> Category -> Date
                    current_description = f"## {category} (cont.)\n### {date_str} (cont.)\n{text}"
                else:
                    current_description += text

    # Flush remaining description
    if current_description:
         current_embed["description"] = current_description
         embeds.append(current_embed)

    return embeds

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send JSON output to Discord as Embeds.")
    parser.add_argument("file_path", help="Path to the JSON output file.")
    parser.add_argument("--exchange", required=True, help="Name of the Exchange (e.g. BSE, NSE Mainboard)")

    args = parser.parse_args()

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL environment variable not set.")
        sys.exit(0)

    if not os.path.exists(args.file_path):
        print(f"File not found: {args.file_path}")
        sys.exit(1)

    try:
        embeds = process_file(args.file_path, args.exchange)
        if embeds:
            send_embeds(webhook_url, embeds)
            print(f"Sent {len(embeds)} embeds to Discord.")
        else:
            print("No filings to send.")

    except Exception as e:
        print(f"Error processing/sending: {e}")
        sys.exit(1)
