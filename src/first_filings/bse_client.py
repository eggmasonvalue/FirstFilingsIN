import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, before_sleep_log
from bse import BSE
from . import config

logger = logging.getLogger(__name__)

class BSEClient:
    def __init__(self):
        self.bse = BSE(download_folder=".")

    @retry(
        stop=stop_after_attempt(config.TOTAL_RETRIES),
        wait=wait_exponential(multiplier=config.RETRY_MULTIPLIER, min=config.RETRY_MIN_DELAY, max=config.RETRY_MAX_DELAY),
        retry=retry_if_exception_type(Exception),
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
