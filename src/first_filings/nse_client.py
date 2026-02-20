import logging
from datetime import datetime
from typing import List, Tuple, Optional
from nse.NSE import NSE
from .exchange import ExchangeClient, Announcement
from . import config

logger = logging.getLogger(__name__)

class NSEClient(ExchangeClient):
    def __init__(self, segment: str = "equities"):
        self.segment = segment
        self.nse = NSE(download_folder=".")

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
                # User said "desc" field. Let's stick to "desc" primarily, maybe check subject if needed.
                # Plan said "desc" field.
                
                is_match = False
                for kw in keywords:
                    if kw.lower() in desc.lower():
                        is_match = True
                        break
                
                if is_match:
                    # Parse date
                    # NSE Format example: "19-Feb-2026 21:31:28" (an_dt) or "19022026213128" (dt)
                    # "an_dt": "19-Feb-2026 21:31:28"
                    dt_str = item.get("an_dt")
                    if dt_str:
                        try:
                            dt = datetime.strptime(dt_str, "%d-%b-%Y %H:%M:%S")
                        except ValueError:
                             try:
                                 # Try "sort_date": "2026-02-19 21:31:28"
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

    def get_enrichment_info(self, scrip_code: str) -> Tuple[str, Optional[str], str]:
        # Scrip code is the symbol.
        # Company name might not be known here if we just have the code, 
        # but the caller usually has the announcement which has the name.
        # We return None for name, allowing caller to use what it has.
        return scrip_code, None, ".NS"
