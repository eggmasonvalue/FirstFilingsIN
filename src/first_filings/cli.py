import click
import logging
from datetime import datetime, timedelta
from . import utils
from .bse_client import BSEClient
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
@click.option('--lookback-years', type=int, default=15, help="Number of years to look back for history.")
def main(date, period, lookback_years):
    """
    Fetch and analyze BSE corporate announcements to identify first-time filings.
    """
    # Setup logging
    utils.setup_logging()

    logger.info(f"Starting FirstFilings with date={date}, period={period}, lookback={lookback_years}")

    result_data = {
        "status": "success",
        "reference_date": date.strftime("%Y-%m-%d"),
        "period": period,
        "lookback_years": lookback_years,
        "filings": {},
        "errors": []
    }

    try:
        from_date, to_date = get_date_range(date, period)
        logger.info(f"Date range: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")

        bse_client = BSEClient()
        analyzer = FirstFilingAnalyzer(bse_client)

        # 1. Fetch announcements for the period
        announcements_by_cat = analyzer.fetch_announcements(from_date, to_date)

        # 2. Check for first filings
        first_filings = {}

        for subcat_label, filings in announcements_by_cat.items():
            if not filings:
                continue

            for filing in filings:
                if not isinstance(filing, dict):
                    continue

                scrip_cd = filing.get("SCRIP_CD")
                longname = filing.get("SLONGNAME")

                if not scrip_cd:
                    logger.warning(f"Skipping filing with no SCRIP_CD: {filing}")
                    continue

                # Determine filing date
                filing_date_str = filing.get("NEWS_DT") or filing.get("NEWS_DATE")
                try:
                    filing_date = (
                        datetime.strptime(filing_date_str, "%d %b %Y")
                        if filing_date_str
                        else to_date
                    )
                except Exception as e:
                    logger.warning(f"Error parsing date {filing_date_str}: {e}. Using reference date.")
                    filing_date = to_date

                try:
                    is_first = analyzer.is_first_filing(
                        scrip_cd, subcat_label, filing_date, lookback_years, longname
                    )

                    if is_first and longname:
                        first_filings.setdefault(subcat_label, []).append(longname)
                        logger.info(f"Found first filing: {subcat_label} - {longname}")

                except Exception as e:
                    error_msg = f"Error checking first filing for {longname}: {e}"
                    logger.error(error_msg)
                    result_data["errors"].append(error_msg)

        result_data["filings"] = first_filings

    except Exception as e:
        logger.exception("Critical error during execution")
        result_data["status"] = "error"
        result_data["errors"].append(str(e))

    # 3. Output JSON
    utils.print_json_output(result_data)

    # 4. Archive
    utils.archive_output(result_data)

if __name__ == "__main__":
    main()
