import logging
from datetime import datetime
from typing import List, Tuple, Optional
from nse import NSE
from .exchange import ExchangeClient, Announcement
from . import config

logger = logging.getLogger(__name__)

class NSEClient(ExchangeClient):
    def __init__(self, segment: str = "equities"):
        self.segment = segment
        self.nse = NSE(download_folder=".", server=True)

    def fetch_announcements(self, from_date: datetime, to_date: datetime, category: str, subcategory: Optional[str] = None, scrip_code: Optional[str] = None) -> List[Announcement]:
        """
        Fetch announcements from NSE and filter by keyword.
        """
        # NSE fetch is for a specific date or date range.
        # The library supports range.

        all_announcements = []

        try:
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

        except Exception as e:
            logger.error(f"Error fetching NSE announcements: {e}")

        return all_announcements

    def get_scrip_info(self, scrip_code: str, announcement_date: datetime) -> dict:
        symbol = scrip_code
        company_name = None
        current_price = None
        current_mkt_cap_cr = None
        price_at_announcement = None

        try:
            # 1. Quote Data
            try:
                quote = self.nse.quote(symbol)
                if quote:
                    info = quote.get("info", {})
                    company_name = info.get("companyName") or company_name # Keep existing if any? No, default is None

                    price_info = quote.get("priceInfo", {})
                    current_price = price_info.get("lastPrice")

                    security_info = quote.get("securityInfo", {})
                    issued_size = security_info.get("issuedSize")

                    if current_price and issued_size:
                        mkt_cap_raw = float(current_price) * float(issued_size)
                        current_mkt_cap_cr = int(round(mkt_cap_raw / 10000000.0))
            except Exception as e:
                logger.warning(f"Error fetching NSE quote for {symbol}: {e}")

            # 2. Historical Price
            try:
                hist_data = self.nse.fetch_equity_historical_data(
                    symbol=symbol,
                    from_date=announcement_date,
                    to_date=announcement_date
                )

                if hist_data and len(hist_data) > 0:
                    price_at_announcement = hist_data[0].get("chClosingPrice")
            except Exception as e:
                logger.warning(f"Error fetching NSE historical data for {symbol}: {e}")

        except Exception as e:
             logger.error(f"Error getting scrip info for {symbol}: {e}")

        return {
            "symbol": symbol,
            "company_name": company_name,
            "current_price": current_price,
            "price_at_announcement": price_at_announcement,
            "current_mkt_cap_cr": current_mkt_cap_cr
        }
