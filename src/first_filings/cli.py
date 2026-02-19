import click
import logging
import json
import sys
from datetime import datetime, timedelta
from . import config
from . import utils 
from .bse_client import BSEClient
# NSEClient import inside main to avoid circular/early import issues if dependencies missing? 
# But we should import it here if we can.
try:
    from .nse_client import NSEClient
except ImportError:
    NSEClient = None

from .core import FirstFilingAnalyzer

logger = logging.getLogger(__name__)

def get_date_range(date_obj, period):
    """
    Calculate from_date and to_date based on period.
    date_obj is datetime object.
    Returns (from_date, to_date).
    """
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
@click.option('-e', '--exchange', type=click.Choice(['bse', 'nse-main', 'nse-sme'], case_sensitive=False), default='bse', help="Exchange to fetch from.")
def main(date, period, lookback_years, analyst_calls, press_releases, presentations, exchange):
    """
    Fetch and analyze corporate announcements to identify first-time filings.
    """
    # Setup logging
    utils.setup_logging()

    # 1. Determine categories
    selected_categories = []
    if analyst_calls:
        if hasattr(config, 'CLI_FLAGS') and 'analyst_calls' in config.CLI_FLAGS:
             selected_categories.append(config.CLI_FLAGS['analyst_calls'])
        else:
             selected_categories.append("Analyst Call Intimation")

    if press_releases:
        if hasattr(config, 'CLI_FLAGS') and 'press_releases' in config.CLI_FLAGS:
             selected_categories.append(config.CLI_FLAGS['press_releases'])
        else:
             selected_categories.append("Press Release")

    if presentations:
        if hasattr(config, 'CLI_FLAGS') and 'presentations' in config.CLI_FLAGS:
             selected_categories.append(config.CLI_FLAGS['presentations'])
        else:
             selected_categories.append("PPT")

    # Default to all if none selected
    if not selected_categories:
        selected_categories = list(config.FILING_SUBCATEGORY.keys())

    logger.info(f"Starting FirstFilings with date={date}, period={period}, lookback={lookback_years}, categories={selected_categories}, exchange={exchange}")

    total_filings_found = 0
    filings_data = {} # Structure: {Category: [filing_dict, ...]}

    try:
        from_date, to_date = get_date_range(date, period)
        logger.info(f"Date range: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")

        exchange_client = None
        if exchange == 'bse':
            exchange_client = BSEClient()
        elif exchange == 'nse-main':
            if NSEClient is None:
                 raise ImportError("NSEClient could not be imported. Ensure 'nse' library is available.")
            exchange_client = NSEClient(segment="equities")
        elif exchange == 'nse-sme':
            if NSEClient is None:
                 raise ImportError("NSEClient could not be imported. Ensure 'nse' library is available.")
            exchange_client = NSEClient(segment="sme")
        
        if not exchange_client:
             raise ValueError(f"Invalid exchange: {exchange}")

        analyzer = FirstFilingAnalyzer(exchange_client)

        # 2. Fetch announcements for the period
        announcements_by_cat = analyzer.fetch_announcements(from_date, to_date, categories=selected_categories)

        # 3. Check for first filings & Enrich
        for category_label, filings in announcements_by_cat.items():
            if not filings:
                continue

            for filing in filings:
                # filing is Announcement object
                scrip_cd = filing.scrip_code
                company_name = filing.company_name
                filing_date_obj = filing.date

                if not scrip_cd:
                    logger.warning(f"Skipping filing with no Scrip Code/Symbol: {filing}")
                    continue

                try:
                    is_first = analyzer.is_first_filing(
                        scrip_cd, category_label, filing_date_obj, lookback_years, company_name
                    )

                    if is_first:
                        logger.info(f"Found first filing: {category_label} - {company_name}")

                        # Enrich Data
                        enriched_data = analyzer.enrich_filing_data(scrip_cd, filing_date_obj, company_name=company_name)

                        if enriched_data:
                            if category_label not in filings_data:
                                filings_data[category_label] = []
                            filings_data[category_label].append(enriched_data)
                            total_filings_found += 1

                except Exception as e:
                    logger.error(f"Error processing filing for {company_name}: {e}")

        # 4. Save Output
        filename = f"{exchange.replace('-', '_')}_output.json"
        output_path = utils.save_output(filings_data, analyzer.failed_checks_count, lookback_years, filename=filename)

        # 5. Print CLI JSON
        utils.print_cli_json(output_path, total_filings_found, analyzer.failed_checks_count)

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
