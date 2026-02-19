import click
import logging
import json
import sys
from datetime import datetime, timedelta
from . import config
from . import utils  # Absolute import issue if run as script, but as package it's fine
from .bse_client import BSEClient
from .core import FirstFilingAnalyzer

logger = logging.getLogger(__name__)

def get_date_range(date_obj, period):
    """
    Calculate from_date and to_date based on period.
    date_obj is datetime object.
    Returns (from_date, to_date).
    """
    # date_obj is datetime.datetime from click.DateTime
    # but we usually need datetime.date for logic, though BSE client handles datetime
    # Let's keep it as datetime for now

    to_date = date_obj

    if period == 'day':
        from_date = to_date
    elif period == 'wtd':
        # Monday of the current week
        from_date = to_date - timedelta(days=to_date.weekday())
    elif period == 'mtd':
        from_date = to_date.replace(day=1)
    elif period == 'qtd':
        month = ((to_date.month - 1) // 3) * 3 + 1
        from_date = to_date.replace(month=month, day=1)
    else:
        # Fallback to day
        from_date = to_date

    return from_date, to_date

@click.command()
@click.option('--date', type=click.DateTime(formats=["%d-%m-%Y", "%Y-%m-%d"]), default=lambda: datetime.now().strftime("%d-%m-%Y"), help="Reference date (DD-MM-YYYY or YYYY-MM-DD). Defaults to today.")
@click.option('--period', type=click.Choice(['day', 'wtd', 'mtd', 'qtd'], case_sensitive=False), default='day', help="Fetch period: day, wtd (week-to-date), mtd (month-to-date), qtd (quarter-to-date).")
@click.option('--lookback-years', type=int, default=2, help="Number of years to look back for history.")
@click.option('-a', '--analyst-calls', is_flag=True, help="Fetch Analyst Call Intimations")
@click.option('-p', '--press-releases', is_flag=True, help="Fetch Press Releases")
@click.option('-t', '--presentations', is_flag=True, help="Fetch Investor Presentations (PPT)")
def main(date, period, lookback_years, analyst_calls, press_releases, presentations):
    """
    Fetch and analyze BSE corporate announcements to identify first-time filings.
    """
    # Setup logging
    utils.setup_logging()

    # 1. Determine categories
    selected_categories = []
    if analyst_calls:
        # Assuming config has these keys map to labels
        # Let's check config keys again. In core.py it iterates config.FILING_SUBCATEGORY.keys()
        # The flags map to specific keys.
        # Based on README: "Analyst Call Intimation", "Press Release", "PPT"
        # We need to map flags to these keys.
        # Let's assume config has constants for these keys or we hardcode them based on known keys.
        # Looking at previous code, it used config.CLI_FLAGS
        if hasattr(config, 'CLI_FLAGS'):
             if 'analyst_calls' in config.CLI_FLAGS: selected_categories.append(config.CLI_FLAGS['analyst_calls'])
        else:
             selected_categories.append("Analyst Call Intimation")

    if press_releases:
        if hasattr(config, 'CLI_FLAGS'):
             if 'press_releases' in config.CLI_FLAGS: selected_categories.append(config.CLI_FLAGS['press_releases'])
        else:
             selected_categories.append("Press Release")

    if presentations:
        if hasattr(config, 'CLI_FLAGS'):
             if 'presentations' in config.CLI_FLAGS: selected_categories.append(config.CLI_FLAGS['presentations'])
        else:
             selected_categories.append("PPT") # Assuming key is PPT based on previous json

    # Default to all if none selected
    if not selected_categories:
        selected_categories = list(config.FILING_SUBCATEGORY.keys())

    logger.info(f"Starting FirstFilings with date={date}, period={period}, lookback={lookback_years}, categories={selected_categories}")

    total_filings_found = 0
    filings_data = {} # Structure: {Category: [filing_dict, ...]}

    try:
        from_date, to_date = get_date_range(date, period)
        logger.info(f"Date range: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")

        bse_client = BSEClient()
        analyzer = FirstFilingAnalyzer(bse_client)

        # 2. Fetch announcements for the period
        announcements_by_cat = analyzer.fetch_announcements(from_date, to_date, categories=selected_categories)

        # 3. Check for first filings & Enrich
        for subcat_label, filings in announcements_by_cat.items():
            if not filings:
                continue

            for filing in filings:
                if not isinstance(filing, dict):
                    continue

                scrip_cd = filing.get("SCRIP_CD")
                longname = filing.get("SLONGNAME")

                # Determine filing date for check
                # API usually returns NEWS_DT in ISO format or similar
                # We need a datetime object for is_first_filing
                filing_dt_str = filing.get("NEWS_DT")
                filing_date_obj = to_date # Default

                if filing_dt_str:
                    try:
                        # Try parsing ISO format first (often returned by API)
                         filing_date_obj = datetime.fromisoformat(filing_dt_str)
                    except ValueError:
                        try:
                            # Fallback formats if any
                            filing_date_obj = datetime.strptime(filing_dt_str, "%Y-%m-%dT%H:%M:%S.%f")
                        except ValueError:
                             pass

                if not scrip_cd:
                    logger.warning(f"Skipping filing with no SCRIP_CD: {filing}")
                    continue

                try:
                    is_first = analyzer.is_first_filing(
                        scrip_cd, subcat_label, filing_date_obj, lookback_years, longname
                    )

                    if is_first:
                        logger.info(f"Found first filing: {subcat_label} - {longname}")

                        # Enrich Data
                        enriched_data = analyzer.enrich_filing_data(scrip_cd, filing_date_obj)

                        if enriched_data:
                            if subcat_label not in filings_data:
                                filings_data[subcat_label] = []
                            filings_data[subcat_label].append(enriched_data)
                            total_filings_found += 1

                except Exception as e:
                    logger.error(f"Error processing filing for {longname}: {e}")

        # 4. Save Output
        output_file = utils.save_output(filings_data, analyzer.failed_checks_count)

        # 5. Print CLI JSON
        utils.print_cli_json(output_file, total_filings_found, analyzer.failed_checks_count)

    except Exception as e:
        logger.exception("Critical error during execution")
        # Print error JSON
        print(json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
