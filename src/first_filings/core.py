import yfinance as yf
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
            
            # If the client supports scrip_code filtering (which they now do),
            # historical_filings should only contain filings for this company.
            
            # The count should be exactly 1 (the current filing being checked)
            # if this is the first time.
            # However, fetch_announcements(to_date=filing_date) might include the current filing.
            # If so, count == 1 means first filing.
            # If count > 1, means previous filings exist.
            # If count == 0, something is wrong (current filing not found? or date mismatch?)
            
            return len(historical_filings) == 1

        except Exception as e:
                logger.error(f"Failed to fetch historical filings for {company_name} - {category_label}: {e}")
                self.failed_checks_count += 1
                return False

    def enrich_filing_data(self, scrip_code, announcement_date_str, company_name=None):
        """
        Enrich filing with symbol, price, and market cap data.
        """
        symbol = None
        # company_name passed in or resolved
        price_at_announcement = None
        current_price = None
        current_mkt_cap_cr = None

        try:
            # 1. Get Enrichment Info from Exchange Client
            sym, name, suffix = self.exchange_client.get_enrichment_info(str(scrip_code))
            
            if sym:
                symbol = sym
            if name and not company_name:
                company_name = name
            
            if not symbol:
                logger.warning(f"Could not find symbol for scrip {scrip_code}")
                return None 

            # 2. Fetch Data from yfinance
            yf_ticker = f"{symbol}{suffix}"
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
            if isinstance(announcement_date_str, str):
                 try:
                     d = datetime.fromisoformat(announcement_date_str)
                     announcement_date = d.date()
                 except Exception:
                     announcement_date = datetime.now().date()
            elif isinstance(announcement_date_str, datetime):
                announcement_date = announcement_date_str.date()
            else: 
                 announcement_date = announcement_date_str

            start_date = announcement_date
            # yfinance history end date is exclusive, so +1 day
            end_date = start_date + timedelta(days=1)
            
            # But wait, strictly speaking we might want price *on* that day.
            # If announcement is during market hours, close price of that day.
            # If after market, close price of that day (or next?).
            # Plan says price *at* announcement. Close price of date is fine.
            
            hist = ticker.history(start=start_date, end=end_date)
            if not hist.empty:
                price_at_announcement = hist['Close'].iloc[0]
            else:
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

