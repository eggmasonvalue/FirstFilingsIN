import logging
import time
from datetime import datetime
from bse import BSE
from . import config
from .exchange import ExchangeClient, Announcement
from .retries import retry_exchange, should_retry_exception


logger = logging.getLogger(__name__)


class BSEClient(ExchangeClient):
    def __init__(self):
        self.bse = BSE(download_folder=".")

    @retry_exchange
    def fetch_paginated_announcements(self, from_date, to_date, category, subcategory, scripcode=None, segment="equity"):
        """
        Fetch all paginated announcements for given filters.
        """
        all_ann = []
        page_count = 1
        total_count = None

        while True:
            try:
                # Add a small delay to be polite and avoid rate limits/timeouts
                time.sleep(0.35)

                # Log fetch attempt
                logger.info(f"Fetching page {page_count} for {subcategory} ({from_date} to {to_date})")

                data = self.bse.announcements(
                    page_no=page_count,
                    from_date=from_date,
                    to_date=to_date,
                    category=category,
                    subcategory=subcategory,
                    scripcode=str(scripcode) if scripcode else None,
                    segment=segment,
                )

                if total_count is None:
                    # Get total count from the first successful response
                    table1 = data.get("Table1")
                    if table1 and isinstance(table1, list) and len(table1) > 0:
                        total_count = table1[0].get("ROWCNT", 0)
                    else:
                        total_count = 0

                page_ann = data.get("Table", [])
                if page_ann:
                    all_ann.extend(page_ann)

                # Check if we have fetched all announcements
                if len(all_ann) >= total_count or not page_ann:
                    break

                page_count += 1

            except Exception as e:
                logger.error(f"Error fetching page {page_count}: {e}")
                raise e # Re-raise to trigger retry

        return all_ann

    def fetch_announcements(self, from_date, to_date, category, subcategory=None, scrip_code=None) -> list[Announcement]:
        """
        Fetch announcements and map to standardized Announcement objects.
        If category is a label (e.g. "Analyst Call Intimation"), fetch all corresponding BSE subcategories.
        """
        all_announcements = []
        
        # Determine subcategories to fetch
        subcats_to_fetch = []
        if subcategory:
            subcats_to_fetch.append(subcategory)
        elif category in config.FILING_SUBCATEGORY:
            subcats_to_fetch = config.FILING_SUBCATEGORY[category]
        else:
            logger.warning(f"Category label '{category}' not found in BSE config. Skipping.")
            return []

        for subcat in subcats_to_fetch:
            try:
                raw_announcements = self.fetch_paginated_announcements(
                    from_date=from_date,
                    to_date=to_date,
                    category=config.FILING_CATEGORY, 
                    subcategory=subcat,
                    scripcode=scrip_code
                )
                
                # Filter if needed (e.g. valid checks or keywords)
                if (
                    subcat == config.SUBCATEGORY_GENERAL
                    and category in config.FILING_SUBCATEGORY_GENERAL_KEYWORD
                ):
                    keyword = config.FILING_SUBCATEGORY_GENERAL_KEYWORD[category]
                    filtered_raw = []
                    for filing in raw_announcements:
                         newssub = filing.get("NEWSSUB") or ""
                         headline = filing.get("HEADLINE") or ""
                         if (keyword.lower() in newssub.lower()) or (keyword.lower() in headline.lower()):
                             filtered_raw.append(filing)
                    raw_announcements = filtered_raw

                for ann in raw_announcements:
                    try:
                        dt_str = ann.get("DT_TM")
                        if dt_str:
                            try:
                                dt = datetime.fromisoformat(dt_str)
                            except ValueError:
                                dt = datetime.now()
                        else:
                            dt = datetime.now()

                        attachment_name = ann.get("ATTACHMENTNAME")
                        attachment_url = None
                        if attachment_name:
                            attachment_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{attachment_name}"

                        all_announcements.append(Announcement(
                            scrip_code=str(ann.get("SCRIP_CD")),
                            company_name=ann.get("SLONGNAME", ""),
                            date=dt,
                            category=category, # Use the high-level label
                            description=ann.get("NEWSSUB") or ann.get("HEADLINE") or "",
                            attachment_url=attachment_url
                        ))
                    except Exception as e:
                        logger.error(f"Error parsing announcement: {e}")
                        continue
            except Exception as e:
                logger.error(f"Error fetching BSE subcategory {subcat}: {e}")
                continue
                
        return all_announcements

    @retry_exchange
    def get_scrip_info(self, scrip_code: str, announcement_date: datetime) -> dict:
        symbol = None
        company_name = None
        current_price = None
        current_mkt_cap_cr = None
        price_at_announcement = None
        financial_snapshot = None

        try:
            # 1. Basic Info
            try:
                lookup_result = self.bse.lookup(str(scrip_code))
                if lookup_result:
                    symbol = lookup_result.get("symbol")
                    company_name = lookup_result.get("company_name")
            except Exception as e:
                 if should_retry_exception(e):
                    raise e
                 logger.warning(f"Error lookup BSE info for {scrip_code}: {e}")

            # 2. Current Price
            try:
                quote = self.bse.quote(str(scrip_code))
                if quote:
                    current_price = quote.get("LTP")
            except Exception as e:
                if should_retry_exception(e):
                    raise e
                logger.warning(f"Error fetching BSE quote for {scrip_code}: {e}")

            # 3. Market Cap
            try:
                trading_info = self.bse.stockTrading(str(scrip_code))
                if trading_info:
                    # Format is like "19,21,678.78"
                    mkt_cap_str = trading_info.get("MktCapFull")
                    if mkt_cap_str:
                        try:
                            current_mkt_cap_cr = float(mkt_cap_str.replace(",", ""))
                        except ValueError:
                            pass
            except Exception as e:
                if should_retry_exception(e):
                    raise e
                logger.warning(f"Error fetching BSE trading info for {scrip_code}: {e}")

            # 4. Financial Snapshot
            try:
                # Assuming bse >= 3.2.0 has financials method
                # We need to verify the exact method name or use the one that provides snapshot
                # In previous versions, it might not be available.
                # Let's try to get financials if available.
                # Based on user request, bse 3.2.0+ provides this.
                # We will store the raw dict or a subset.
                if hasattr(self.bse, 'financials'):
                     financials = self.bse.financials(str(scrip_code))
                     if financials:
                         financial_snapshot = financials
            except Exception as e:
                if should_retry_exception(e):
                    raise e
                logger.warning(f"Error fetching BSE financials for {scrip_code}: {e}")
            
            # 5. Historical Price
            # T12M data
            try:
                hist_data = self.bse.equityPriceVolumeT12M(str(scrip_code))
                if hist_data and "Data" in hist_data and "data" in hist_data["Data"]:
                     # data is list of [DateStr, Price, Vol]
                     # DateStr format: 'Thu Feb 20 2025 00:00:00'
                     target_date = announcement_date.date()

                     rows = hist_data["Data"]["data"]
                     best_date = None

                     for row in rows:
                         if len(row) >= 2:
                             d_str = row[0]
                             p_str = row[1]
                             try:
                                 # Date format: 'Thu Feb 20 2025 00:00:00'
                                 d = datetime.strptime(d_str, "%a %b %d %Y %H:%M:%S").date()

                                 if d <= target_date:
                                     # Keep track of the latest available trading date up to the announcement
                                     if best_date is None or d > best_date:
                                         best_date = d
                                         price_at_announcement = float(p_str)
                             except ValueError:
                                 continue
            except Exception as e:
                if should_retry_exception(e):
                    raise e
                logger.warning(f"Error fetching BSE historical data for {scrip_code}: {e}")

        except Exception as e:
            if should_retry_exception(e):
                 raise e
            logger.error(f"Error getting scrip info for {scrip_code}: {e}")

        return {
            "symbol": symbol,
            "company_name": company_name,
            "current_price": current_price,
            "price_at_announcement": price_at_announcement,
            "current_mkt_cap_cr": current_mkt_cap_cr,
            "financial_snapshot": financial_snapshot
        }
