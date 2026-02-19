from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional

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
    def get_enrichment_info(self, scrip_code: str) -> Tuple[str, Optional[str], str]:
        """
        Returns (symbol, company_name, yfinance_suffix)
        """
        pass
