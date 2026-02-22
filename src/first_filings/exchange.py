from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Announcement:
    scrip_code: str
    company_name: str
    date: datetime
    category: str
    description: str
    attachment_url: Optional[str] = None

class ExchangeClient(ABC):
    @abstractmethod
    def fetch_announcements(self, from_date: datetime, to_date: datetime, category: str, subcategory: Optional[str] = None, scrip_code: Optional[str] = None) -> List[Announcement]:
        pass

    @abstractmethod
    def get_scrip_info(self, scrip_code: str, announcement_date: datetime) -> dict:
        """
        Returns a dictionary with:
        symbol, company_name, current_price, price_at_announcement, current_mkt_cap_cr
        """
        pass
