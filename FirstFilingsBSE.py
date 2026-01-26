from datetime import datetime, timedelta
from bse import BSE
import time

TOTAL_RETRIES = 5  # Number of retries for fetching filings
RETRY_DELAY = 3  # Delay in seconds between retries

filing_category = "Company Update"
subcategory_general = "General"

filing_subcategory = {
    "Analyst Call Intimation": ["Analyst / Investor Meet"],
    "Press Release": [
        "Press Release / Media Release",
        #     "Press Release / Media Release (Revised)",
        #     "Press release (Revised)"
        #     it can't be the first filing if it is a revised press release
        #     likely to not be a catch-all since a lot of general category announcements could contain press release style information
    ],
    "PPT": ["Investor Presentation", subcategory_general],
}

filing_subcategory_general_keyword = {
    # "Analyst Call Intimation":
    #     "Analyst / Investor Meet",
    # "Press Release":"Release",
    "PPT": "Presentation"
}


def fetch_paginated_announcements(
    bse, from_date, to_date, category, subcategory, scripcode=None, segment="equity"
):
    """Fetch all paginated announcements for given filters."""
    all_ann = []
    page_count = 1
    total_count = None
    while True:
        try:
            data = bse.announcements(
                page_no=page_count,
                from_date=from_date,
                to_date=to_date,
                category=category,
                subcategory=subcategory,
                scripcode=str(scripcode) if scripcode else None,
                segment=segment,
            )
            if total_count is None:
                total_count = (
                    data.get("Table1", [{}])[0].get("ROWCNT", 0)
                    if data.get("Table1")
                    else 0
                )
            page_ann = data.get("Table", [])
            all_ann.extend(page_ann)
            if len(all_ann) >= total_count or not page_ann:
                break
            page_count += 1
        except Exception as e:
            return f"Error: {e}"
    return all_ann


def fetch_announcements_for_date(bse, date: datetime):
    """Fetch all announcements for each subcategory on a given date."""
    print(f"Fetching announcements for {date.strftime('%Y-%m-%d')} ...")
    results = {}
    for subcat_label, subcats in filing_subcategory.items():
        results_list = []
        for subcat in subcats:
            # key = f"{subcat_label} - {subcat}"
            # print(key)
            retries = 0
            ann = None
            while retries < TOTAL_RETRIES:
                ann = fetch_paginated_announcements(
                    bse,
                    from_date=date,
                    to_date=date,
                    category=filing_category,
                    subcategory=subcat,
                )
                # Improved error check: treat only str as error, otherwise treat as valid result
                if isinstance(ann, str):
                    print(
                        f"  Error fetching announcements for {subcat_label} - {subcat}: {ann} (retry {retries + 1}/{TOTAL_RETRIES})"
                    )
                    retries += 1
                    time.sleep(RETRY_DELAY)
                elif isinstance(ann, list):
                    # print(f"  Successfully fetched announcements for {subcat_label} - {subcat}")
                    break
                else:
                    print(
                        f"  Unexpected result type for {subcat_label} - {subcat}: {type(ann)}. Skipping."
                    )
                    ann = []
                    break
            if isinstance(ann, str):
                print(
                    f"  Failed to fetch announcements for {subcat_label} - {subcat} after {TOTAL_RETRIES} retries, skipping."
                )
                continue

            # Only filter if ann is a list (not an error string)
            if isinstance(ann, list):
                # For 'General' subcategory, filter by keyword in NEWSSUB or HEADLINE
                if (
                    subcat == subcategory_general
                    and subcat_label in filing_subcategory_general_keyword
                ):
                    keyword = filing_subcategory_general_keyword[subcat_label]
                    ann = [
                        filing
                        for filing in ann
                        if (
                            (
                                isinstance(filing, dict)
                                and filing.get("NEWSSUB")
                                and keyword.lower() in filing["NEWSSUB"].lower()
                            )
                            or (
                                isinstance(filing, dict)
                                and filing.get("HEADLINE")
                                and keyword.lower() in filing["HEADLINE"].lower()
                            )
                        )
                    ]
                results_list.extend(ann)
        results[subcat_label] = results_list
    print("Done fetching all announcements for the date.")
    return results


def is_first_filing(bse, scrip_cd, subcat_label, input_date, lookback_years, longname):
    """Check if this is the first filing for the scrip/subcategory label in the lookback period."""
    lookback_start = input_date - timedelta(days=lookback_years * 365)
    print(
        f" Checking if it is the first {subcat_label} for {longname} in the last {lookback_years} years ..."
    )
    all_filings = []
    for subcat_values in filing_subcategory[subcat_label]:
        retries = 0
        filings = None
        while retries < TOTAL_RETRIES:
            filings = fetch_paginated_announcements(
                bse,
                from_date=lookback_start,
                to_date=input_date,
                category=filing_category,
                subcategory=subcat_values,
                scripcode=scrip_cd,
            )
            # Improved error check: treat only str as error, otherwise treat as valid result
            if isinstance(filings, str):
                print(
                    f"    Error fetching filings for {longname}: {filings} (retry {retries + 1}/{TOTAL_RETRIES})"
                )
                retries += 1
                time.sleep(RETRY_DELAY)
            elif isinstance(filings, list):
                # print(f"    Successfully fetched filings for {longname} - {subcat_values}")
                break
            else:
                print(
                    f"    Unexpected result type for {longname} - {subcat_values}: {type(filings)}. Skipping."
                )
                filings = []
                break
        if isinstance(filings, str):
            print(
                f"    Failed to fetch filings for {subcat_values} after {TOTAL_RETRIES} retries, skipping."
            )
            continue

        # dump into json file for debugging
        # with open(f"filings_{scrip_cd}_{subcat_label}.json", "w") as f:
        #     import json
        #     json.dump(filings, f, indent=4)
        # For 'General' subcategory, filter by keyword in NEWSSUB or HEADLINE
        if (
            subcat_values == subcategory_general
            and subcat_label in filing_subcategory_general_keyword
        ):
            keyword = filing_subcategory_general_keyword[subcat_label]
            filings = [
                filing
                for filing in filings
                if (
                    (
                        isinstance(filing, dict)
                        and filing.get("NEWSSUB")
                        and keyword.lower() in filing["NEWSSUB"].lower()
                    )
                    or (
                        isinstance(filing, dict)
                        and filing.get("HEADLINE")
                        and keyword.lower() in filing["HEADLINE"].lower()
                    )
                )
            ]
        all_filings.extend(filings)
    # Defensive: Only return True if there is exactly one filing, and at least one subcat succeeded
    if all_filings:
        return len(all_filings) == 1
    else:
        return False


def parse_date_range(args):
    """
    Parse CLI arguments for date range options.
    Returns (from_date, to_date, lookback_years).
    """
    from datetime import datetime, timedelta

    # Defaults
    input_date = datetime.now()
    from_date = input_date
    to_date = input_date
    lookback_years = 15

    # Helper to parse date string (now expects DD-MM-YYYY)
    def parse_dt(s):
        return datetime.strptime(s, "%d-%m-%Y")

    # Option parsing (date is always to_date)
    if "-WTD" in args:
        idx = args.index("-WTD")
        to_date = parse_dt(args[idx + 1])
        # Week: Monday to Sunday containing to_date, but to_date is the end
        weekday = to_date.weekday()
        from_date = to_date - timedelta(days=weekday)
    elif "-D" in args:
        idx = args.index("-D")
        to_date = parse_dt(args[idx + 1])
        from_date = to_date
    elif "-MTD" in args:
        idx = args.index("-MTD")
        to_date = parse_dt(args[idx + 1])
        from_date = to_date.replace(day=1)
    elif "-QTD" in args:
        idx = args.index("-QTD")
        to_date = parse_dt(args[idx + 1])
        month = ((to_date.month - 1) // 3) * 3 + 1
        from_date = to_date.replace(month=month, day=1)
    else:
        # Default: positional date argument or today
        if len(args) > 1 and not args[1].startswith("-"):
            to_date = parse_dt(args[1])
            from_date = to_date

    # Lookback years
    for i, arg in enumerate(args):
        if arg.isdigit():
            lookback_years = int(arg)
        elif arg.startswith("--lookback="):
            lookback_years = int(arg.split("=")[1])

    return from_date, to_date, lookback_years


def main():
    import sys

    # Usage: python FirstFilingsToday.py [-W|-D|-M|-Q] YYYY-MM-DD [LOOKBACK_YEARS]
    args = sys.argv
    from_date, to_date, lookback_years = parse_date_range(args)
    print(
        f"Starting: BSE First Filings from {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')} with lookback period {lookback_years} years..."
    )
    bse = BSE(download_folder=".")
    announcements = fetch_announcements_for_date_range(bse, from_date, to_date)

    # dump to json file for debugging
    # with open(f"announcements_{input_date.strftime('%Y-%m-%d')}.json", "w") as f:
    #     import json
    #     json.dump(announcements, f, indent=4)

    first_filings = {}
    for subcat_label, filings in announcements.items():
        if not isinstance(filings, list):
            continue
        for filing in filings:
            scrip_cd = filing.get("SCRIP_CD")
            longname = filing.get("SLONGNAME")
            if not scrip_cd:
                continue
            # Use the filing date for lookback, fallback to to_date
            filing_date_str = filing.get("NEWS_DT") or filing.get("NEWS_DATE")
            try:
                filing_date = (
                    datetime.strptime(filing_date_str, "%d %b %Y")
                    if filing_date_str
                    else to_date
                )
            except Exception:
                filing_date = to_date
            is_first = is_first_filing(
                bse, scrip_cd, subcat_label, filing_date, lookback_years, longname
            )
            if is_first and longname:
                first_filings.setdefault(subcat_label, []).append(longname)

    # Highlighted output
    print("\n" + "*" * 80)
    print(
        "First filings in the last {} years for range {} to {}:".format(
            lookback_years, from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")
        )
    )
    if first_filings:
        for subcat_label, names in first_filings.items():
            for name in names:
                print(f"  {subcat_label:<20} : {name}")
    else:
        print("  None")
    print("*" * 80 + "\n")


# New function to fetch announcements for a date range
def fetch_announcements_for_date_range(bse, from_date, to_date):
    """Fetch all announcements for each subcategory in a date range."""
    print(
        f"Fetching announcements from {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')} ..."
    )
    results = {}
    for subcat_label, subcats in filing_subcategory.items():
        results_list = []
        for subcat in subcats:
            retries = 0
            ann = None
            while retries < TOTAL_RETRIES:
                ann = fetch_paginated_announcements(
                    bse,
                    from_date=from_date,
                    to_date=to_date,
                    category=filing_category,
                    subcategory=subcat,
                )
                if isinstance(ann, str):
                    print(
                        f"  Error fetching announcements for {subcat_label} - {subcat}: {ann} (retry {retries + 1}/{TOTAL_RETRIES})"
                    )
                    retries += 1
                    time.sleep(RETRY_DELAY)
                elif isinstance(ann, list):
                    break
                else:
                    print(
                        f"  Unexpected result type for {subcat_label} - {subcat}: {type(ann)}. Skipping."
                    )
                    ann = []
                    break
            if isinstance(ann, str):
                print(
                    f"  Failed to fetch announcements for {subcat_label} - {subcat} after {TOTAL_RETRIES} retries, skipping."
                )
                continue
            if isinstance(ann, list):
                # For 'General' subcategory, filter by keyword in NEWSSUB or HEADLINE
                if (
                    subcat == subcategory_general
                    and subcat_label in filing_subcategory_general_keyword
                ):
                    keyword = filing_subcategory_general_keyword[subcat_label]
                    ann = [
                        filing
                        for filing in ann
                        if (
                            (
                                isinstance(filing, dict)
                                and filing.get("NEWSSUB")
                                and keyword.lower() in filing["NEWSSUB"].lower()
                            )
                            or (
                                isinstance(filing, dict)
                                and filing.get("HEADLINE")
                                and keyword.lower() in filing["HEADLINE"].lower()
                            )
                        )
                    ]
                results_list.extend(ann)
        results[subcat_label] = results_list
    print("Done fetching all announcements for the date range.")
    return results


if __name__ == "__main__":
    main()
