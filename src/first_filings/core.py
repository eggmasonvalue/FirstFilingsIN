import yfinance as yf
from datetime import datetime, timedelta
import logging
from . import config
from .bse_client import BSEClient

logger = logging.getLogger(__name__)

class FirstFilingAnalyzer:
    def __init__(self, bse_client: BSEClient):
        self.bse_client = bse_client
        self.failed_checks_count = 0

    def _filter_announcements(self, announcements, subcat_label, subcat_value):
        """
        Filter announcements based on keywords if applicable.
        """
        if not announcements:
            return []

        if (
            subcat_value == config.SUBCATEGORY_GENERAL
            and subcat_label in config.FILING_SUBCATEGORY_GENERAL_KEYWORD
        ):
            keyword = config.FILING_SUBCATEGORY_GENERAL_KEYWORD[subcat_label]
            filtered = []
            for filing in announcements:
                if not isinstance(filing, dict):
                    continue

                newssub = filing.get("NEWSSUB") or ""
                headline = filing.get("HEADLINE") or ""

                if (keyword.lower() in newssub.lower()) or (keyword.lower() in headline.lower()):
                    filtered.append(filing)
            return filtered

        return announcements

    def fetch_announcements(self, from_date, to_date, categories=None):
        """
        Fetch all announcements for each subcategory in a date range.
        Returns a dict: {subcategory_label: [announcements]}

        :param categories: List of category labels to fetch. If None, fetch all.
        """
        logger.info(f"Fetching announcements from {from_date} to {to_date}")
        results = {}

        target_categories = categories if categories else config.FILING_SUBCATEGORY.keys()

        for subcat_label in target_categories:
            if subcat_label not in config.FILING_SUBCATEGORY:
                logger.warning(f"Category {subcat_label} not found in config.")
                continue

            subcats = config.FILING_SUBCATEGORY[subcat_label]
            results_list = []

            for subcat in subcats:
                try:
                    ann = self.bse_client.fetch_paginated_announcements(
                        from_date=from_date,
                        to_date=to_date,
                        category=config.FILING_CATEGORY,
                        subcategory=subcat,
                    )

                    filtered_ann = self._filter_announcements(ann, subcat_label, subcat)
                    results_list.extend(filtered_ann)

                except Exception as e:
                    logger.error(f"Failed to fetch announcements for {subcat_label} - {subcat}: {e}")
                    continue

            results[subcat_label] = results_list

        return results

    def is_first_filing(self, scrip_cd, subcat_label, filing_date, lookback_years, longname):
        """
        Check if this is the first filing for the scrip/subcategory label in the lookback period.
        """
        lookback_start = filing_date - timedelta(days=lookback_years * 365)
        logger.info(f"Checking if first {subcat_label} for {longname} ({scrip_cd}) since {lookback_start}")

        all_filings = []
        try:
            for subcat_value in config.FILING_SUBCATEGORY.get(subcat_label, []):
                filings = self.bse_client.fetch_paginated_announcements(
                    from_date=lookback_start,
                    to_date=filing_date,
                    category=config.FILING_CATEGORY,
                    subcategory=subcat_value,
                    scripcode=scrip_cd,
                )

                filtered_filings = self._filter_announcements(filings, subcat_label, subcat_value)
                all_filings.extend(filtered_filings)
        except Exception as e:
                logger.error(f"Failed to fetch historical filings for {longname} - {subcat_value}: {e}")
                self.failed_checks_count += 1
                # Safest is to assume it's NOT a first filing if we can't verify history.
                return False

        # If exactly one filing is found (the current one), then it is the first filing.
        return len(all_filings) == 1

    def enrich_filing_data(self, scrip_code, announcement_date_str):
        """
        Enrich filing with symbol, price, and market cap data.
        """
        symbol = None
        company_name = None
        price_at_announcement = None
        current_price = None
        current_mkt_cap_cr = None

        try:
            # 1. Get Symbol and Company Name from BSE
            lookup_result = self.bse_client.bse.lookup(str(scrip_code))
            if lookup_result:
                symbol = lookup_result.get("symbol")
                company_name = lookup_result.get("company_name")

            if not symbol:
                logger.warning(f"Could not find symbol for scrip {scrip_code}")
                return None # Should we fail or return partial? Let's return partial.

            # 2. Fetch Data from yfinance
            yf_ticker = f"{symbol}.BO"
            ticker = yf.Ticker(yf_ticker)

            # Fetch Current Data
            info = ticker.info
            current_price = info.get("currentPrice")
            # If currentPrice is missing, try previousClose
            if current_price is None:
                current_price = info.get("previousClose")

            mkt_cap_raw = info.get("marketCap")
            if mkt_cap_raw:
                current_mkt_cap_cr = int(round(mkt_cap_raw / 10000000)) # Convert to Crores

            # Fetch Historical Price
            # announcement_date_str is likely datetime object or string.
            # In cli.py it seems dates are passed around as datetime objects usually, but let's check input.
            # Looking at is_first_filing call, filing_date is a date/datetime object.

            # We need the date object
            if isinstance(announcement_date_str, str):
                 try:
                     # Attempt generic ISO parse if string
                     d = datetime.fromisoformat(announcement_date_str)
                     announcement_date = d.date()
                 except:
                     # Fallback
                     announcement_date = datetime.now().date()
            elif isinstance(announcement_date_str, datetime):
                announcement_date = announcement_date_str.date()
            else: # Date object
                 announcement_date = announcement_date_str

            start_date = announcement_date
            end_date = start_date + timedelta(days=1)

            hist = ticker.history(start=start_date, end=end_date)
            if not hist.empty:
                price_at_announcement = hist['Close'].iloc[0]
            else:
                # Try getting previous trading day if today is holiday/weekend?
                # Or just leave as None. Requirement: "price will be a column"
                # Let's try up to 3 days back if empty?
                # User said: "Ideally i don't want price on date of announcement" -> "I want market cap on date of announcement and current market cap but if yfinance doesn't provide historical market cap, we may have to stick to two prices and one market cap structure."
                # So we stick to price on date.
                pass

        except Exception as e:
            logger.error(f"Error enriching data for {scrip_code}: {e}")

        return {
            "scrip_code": str(scrip_code),
            "company_name": company_name,
            "date": announcement_date.isoformat(),
            "price_at_announcement": price_at_announcement,
            "current_price": current_price,
            "current_mkt_cap_cr": current_mkt_cap_cr
        }
