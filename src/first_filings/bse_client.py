import logging
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception, before_sleep_log
from bse import BSE
from . import config
from .exchange import ExchangeClient, Announcement


logger = logging.getLogger(__name__)


def should_retry(exception):
    """
    Custom retry predicate.
    Retries on TimeoutError.
    Retries on ConnectionError if status code is not 4xx (except 429).
    Retries on other Exceptions.
    """
    if isinstance(exception, TimeoutError):
        return True

    if isinstance(exception, ConnectionError):
        # Try to parse status code from message
        try:
            msg = str(exception)
            # Message format is "STATUS_CODE: REASON" e.g. "404: Not Found"
            if ":" in msg:
                status_code_str = msg.split(":")[0]
                status_code = int(status_code_str)

                if status_code == 429:
                    return True
                if 400 <= status_code < 500:
                    return False  # Stop on client errors (400, 401, 403, 404, etc)
            return True  # Retry on 5xx or other codes
        except ValueError:
            return True  # If parsing fails, default to retry

    # Retry on other unexpected exceptions
    return True


class BSEClient(ExchangeClient):
    def __init__(self):
        self.bse = BSE(download_folder=".")

    @retry(
        stop=stop_after_attempt(config.TOTAL_RETRIES),
        wait=wait_random_exponential(multiplier=1, min=config.RETRY_MIN_DELAY, max=config.RETRY_MAX_DELAY),
        retry=retry_if_exception(should_retry),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def fetch_paginated_announcements(self, from_date, to_date, category, subcategory, scripcode=None, segment="equity"):
        """
        Fetch all paginated announcements for given filters.
        """
        all_ann = []
        page_count = 1
        total_count = None

        # Use a loop to handle pagination, but the retry logic applies to the *entire fetch process* if any page fails?
        # Or should we retry per page?
        # The original code retries the whole function. Let's stick to that, but retry logic is handled by tenacity now.

        while True:
            try:
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
            # Maybe it's a direct category or we don't know mapping?
            # For BSE client, we usually rely on config. 
            # If not found, log warning? Or assume it's a direct subcategory string?
            # Existing logic suggests category is the broad type (e.g. "Corp") and subcategory is specific.
            # But here 'category' arg is mapped to 'subcat_label'.
            logger.warning(f"Category label '{category}' not found in BSE config. Skipping.")
            return []

        for subcat in subcats_to_fetch:
            try:
                # Note: BSE.announcements takes 'category' as the broad BSE category (e.g. 'Corp. Action')
                # and 'subcategory' as the specific type.
                # In config.py: FILING_CATEGORY = "Corp. Action"
                # So we use config.FILING_CATEGORY for the 'category' arg of BSE.announcements
                
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

                        all_announcements.append(Announcement(
                            scrip_code=str(ann.get("SCRIP_CD")),
                            company_name=ann.get("SLONGNAME", ""),
                            date=dt,
                            category=category, # Use the high-level label
                            description=ann.get("NEWSSUB") or ann.get("HEADLINE") or "",
                            attachment_url=ann.get("ATTACHMENTNAME")
                        ))
                    except Exception as e:
                        logger.error(f"Error parsing announcement: {e}")
                        continue
            except Exception as e:
                logger.error(f"Error fetching BSE subcategory {subcat}: {e}")
                continue
                
        return all_announcements

    def get_enrichment_info(self, scrip_code: str):
        lookup_result = self.bse.lookup(str(scrip_code))
        symbol = None
        company_name = None
        
        if lookup_result:
            symbol = lookup_result.get("symbol")
            company_name = lookup_result.get("company_name")
            
        return symbol, company_name, ".BO"

