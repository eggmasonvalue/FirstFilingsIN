from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict
from . import config
from .exchange import ExchangeClient, Announcement

logger = logging.getLogger(__name__)

class FirstFilingAnalyzer:
    def __init__(self, exchange_client: ExchangeClient):
        self.exchange_client = exchange_client
        self.failed_checks_count = 0

    def fetch_announcements(self, from_date: datetime, to_date: datetime, categories: Optional[List[str]] = None) -> Dict[str, List[Announcement]]:
        """
        Fetch all announcements for each category label in a date range.
        Returns a dict: {category_label: [Announcement]}
        """
        logger.info(f"Fetching announcements from {from_date} to {to_date}")
        results = {}

        target_categories = categories if categories else config.FILING_SUBCATEGORY.keys()

        for category_label in target_categories:
            try:
                # Delegate fetching/filtering to the client
                results_list = self.exchange_client.fetch_announcements(
                    from_date=from_date,
                    to_date=to_date,
                    category=category_label
                )
                results[category_label] = results_list

            except Exception as e:
                logger.error(f"Failed to fetch announcements for {category_label}: {e}")
                continue

        return results

    def is_first_filing(self, scrip_code, category_label, filing_date, lookback_years, company_name):
        """
        Check if this is the first filing for the scrip/category label in the lookback period.
        """
        lookback_start = filing_date - timedelta(days=lookback_years * 365)
        logger.info(f"Checking if first {category_label} for {company_name} ({scrip_code}) since {lookback_start}")

        try:
            # Fetch history
            historical_filings = self.exchange_client.fetch_announcements(
                from_date=lookback_start,
                to_date=filing_date, # inclusive?
                category=category_label,
                scrip_code=scrip_code
            )
            
            return len(historical_filings) == 1

        except Exception as e:
                logger.error(f"Failed to fetch historical filings for {company_name} - {category_label}: {e}")
                self.failed_checks_count += 1
                return False

    def enrich_filing_data(self, scrip_code, announcement_date_str, company_name=None):
        """
        Enrich filing with symbol, price, and market cap data.
        """
        # Parse date
        if isinstance(announcement_date_str, str):
             try:
                 d = datetime.fromisoformat(announcement_date_str)
                 announcement_date = d
             except Exception:
                 announcement_date = datetime.now()
        elif isinstance(announcement_date_str, datetime):
            announcement_date = announcement_date_str
        else:
             announcement_date = datetime.now()

        # Initialize result
        enriched_info = {
            "symbol": None,
            "company_name": company_name,
            "current_price": None,
            "price_at_announcement": None,
            "current_mkt_cap_cr": None
        }

        try:
            # Get Enrichment Info from Exchange Client
            info = self.exchange_client.get_scrip_info(str(scrip_code), announcement_date)
            
            if info:
                enriched_info.update({
                    "symbol": info.get("symbol"),
                    "current_price": info.get("current_price"),
                    "price_at_announcement": info.get("price_at_announcement"),
                    "current_mkt_cap_cr": info.get("current_mkt_cap_cr")
                })
                # Only update company name if present in info, else keep original
                if info.get("company_name"):
                    enriched_info["company_name"] = info.get("company_name")
            
            if not enriched_info["symbol"]:
                logger.warning(f"Could not find symbol for scrip {scrip_code}")
                return None

        except Exception as e:
            logger.error(f"Error enriching data for {scrip_code}: {e}")
            return None

        return {
            "scrip_code": str(scrip_code),
            "company_name": enriched_info["company_name"],
            "date": announcement_date.isoformat(),
            "price_at_announcement": enriched_info["price_at_announcement"],
            "current_price": enriched_info["current_price"],
            "current_mkt_cap_cr": enriched_info["current_mkt_cap_cr"]
        }
