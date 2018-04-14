
# Standard
import re
import os

# Third Party
import requests
from requests import Response, HTTPError

# Local
from xis.xerocraft_org_utils.xerocraftscraper import XerocraftScraper


class PaypalScraper(XerocraftScraper):

    def __init__(self):
        # Only the production xerocraft.org server has purchase info to scrape.
        super().__init__(server_override=XerocraftScraper.SERVER_PROD)

    def scrape_agreement_ids(self):

        # Attempt to log into xerocraft.org using an account that has access to treasurer tools:
        post_data = { "XSC": XerocraftScraper.get_token() }
        url = "https://www.xerocraft.org/JSONP.php"

        response = requests.post(url,data=post_data)  # type: Response
        try:
            response.raise_for_status()
        except HTTPError as e:
            self.logger.exception(e)
            return []

        # Scrape PayPal Agreement IDs from the response text.
        # The format of the agreementID is unique enough that we probably don't need any guarding context.
        pattern = "I-[A-Z0-9]{12}"  # The format of a PayPal agreement ID
        matches = re.findall(pattern, response.text)
        return list(set(matches))

