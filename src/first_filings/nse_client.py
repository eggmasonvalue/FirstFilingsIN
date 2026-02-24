import logging
from datetime import datetime, timedelta
from typing import List, Optional
from nse import NSE
from .exchange import ExchangeClient, Announcement
from . import config
from .retries import retry_exchange, should_retry_exception

logger = logging.getLogger(__name__)

class NSEClient(ExchangeClient):
    def __init__(self, segment: str = "equities"):
        self.segment = segment
        self.nse = NSE(download_folder=".", server=True)

    @retry_exchange
    def fetch_announcements(self, from_date: datetime, to_date: datetime, category: str, subcategory: Optional[str] = None, scrip_code: Optional[str] = None) -> List[Announcement]:
        """
        Fetch announcements from NSE and filter by keyword.
        """
        # NSE fetch is for a specific date or date range.
        # The library supports range.

        all_announcements = []

        logger.info(f"Fetching NSE announcements for {self.segment} from {from_date} to {to_date}")
        raw_data = self.nse.announcements(
            index=self.segment,
            from_date=from_date,
            to_date=to_date,
            symbol=scrip_code
        )

        # Filter and Map
        # detailed category mapping
        keywords = []
        if subcategory:
            keywords = config.NSE_CATEGORY_KEYWORDS.get(subcategory, [])
        elif category in config.NSE_CATEGORY_KEYWORDS:
             # If only category is passed (though logic usually passes subcategory)
             keywords = config.NSE_CATEGORY_KEYWORDS.get(category, [])

        if not keywords and subcategory:
             # Fallback/Log if no keywords defined
             logger.warning(f"No keywords defined for subcategory: {subcategory}")

        for item in raw_data:
            desc = item.get("desc", "")

            is_match = False
            for kw in keywords:
                if kw.lower() in desc.lower():
                    is_match = True
                    break

            if is_match:
                # Parse date
                dt_str = item.get("an_dt")
                if dt_str:
                    try:
                        dt = datetime.strptime(dt_str, "%d-%b-%Y %H:%M:%S")
                    except ValueError:
                         try:
                             dt_str_sort = item.get("sort_date")
                             dt = datetime.strptime(dt_str_sort, "%Y-%m-%d %H:%M:%S")
                         except Exception:
                            dt = datetime.now()
                else:
                    dt = datetime.now()

                all_announcements.append(Announcement(
                    scrip_code=item.get("symbol"),
                    company_name=item.get("sm_name", ""),
                    date=dt,
                    category=subcategory if subcategory else category,
                    description=desc,
                    attachment_url=item.get("attchmntFile")
                ))

        return all_announcements

    @retry_exchange
    def get_scrip_info(self, scrip_code: str, announcement_date: datetime) -> dict:
        symbol = scrip_code
        company_name = None
        current_price = None
        current_mkt_cap_cr = None
        price_at_announcement = None

        # Keep track of active series to fetch history
        active_series = 'EQ'

        try:
            # 1. Quote Data
            try:
                quote = self.nse.quote(symbol)
                if quote:
                    info = quote.get("info", {})
                    company_name = info.get("companyName") or company_name # Keep existing if any? No, default is None

                    # Determine active series
                    # info.get('activeSeries') returns list like ['BE']
                    series_list = info.get('activeSeries', [])
                    if 'EQ' in series_list:
                        active_series = 'EQ'
                    elif series_list:
                        active_series = series_list[0]

                    price_info = quote.get("priceInfo", {})
                    current_price = price_info.get("lastPrice")

                    security_info = quote.get("securityInfo", {})
                    issued_size = security_info.get("issuedSize")

                    if current_price and issued_size:
                        mkt_cap_raw = float(current_price) * float(issued_size)
                        current_mkt_cap_cr = int(round(mkt_cap_raw / 10000000.0))
            except Exception as e:
                if should_retry_exception(e):
                    raise e
                logger.warning(f"Error fetching NSE quote for {symbol}: {e}")

            # 2. Historical Price
            try:
                # Use a lookback window (e.g., 7 days) to find the nearest trading day
                from_d = announcement_date - timedelta(days=7)
                to_d = announcement_date

                hist_data = self.nse.fetch_equity_historical_data(
                    symbol=symbol,
                    from_date=from_d,
                    to_date=to_d,
                    series=active_series
                )

                if hist_data and len(hist_data) > 0:
                    # Data is returned in ascending order by date; use the latest available
                    price_at_announcement = hist_data[-1].get("chClosingPrice")
            except Exception as e:
                if should_retry_exception(e):
                    raise e
                logger.warning(f"Error fetching NSE historical data for {symbol}: {e}")

        except Exception as e:
             if should_retry_exception(e):
                 raise e
             logger.error(f"Error getting scrip info for {symbol}: {e}")

        return {
            "symbol": symbol,
            "company_name": company_name,
            "current_price": current_price,
            "price_at_announcement": price_at_announcement,
            "current_mkt_cap_cr": current_mkt_cap_cr
        }
