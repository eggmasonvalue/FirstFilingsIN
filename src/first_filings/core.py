from datetime import timedelta
import logging
from . import config
from .bse_client import BSEClient

logger = logging.getLogger(__name__)

class FirstFilingAnalyzer:
    def __init__(self, bse_client: BSEClient):
        self.bse_client = bse_client

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

    def fetch_announcements(self, from_date, to_date):
        """
        Fetch all announcements for each subcategory in a date range.
        Returns a dict: {subcategory_label: [announcements]}
        """
        logger.info(f"Fetching announcements from {from_date} to {to_date}")
        results = {}

        for subcat_label, subcats in config.FILING_SUBCATEGORY.items():
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
                    # Continue to next subcategory even if one fails?
                    # Yes, to be robust.
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
        for subcat_value in config.FILING_SUBCATEGORY.get(subcat_label, []):
            try:
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
                 # If we fail to fetch history, we can't determine if it's first.
                 # To be safe, maybe return False? Or log and continue?
                 # If we miss history, we might falsely report a first filing.
                 # Safest is to assume it's NOT a first filing if we can't verify history.
                 return False

        # If exactly one filing is found (the current one), then it is the first filing.
        # Note: fetch_paginated_announcements returns filings in the range [lookback_start, filing_date].
        # So the current filing should be in the list.
        return len(all_filings) == 1
