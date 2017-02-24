
# Standard
import re
import os

# Third Party
from requests import Response, HTTPError

# Local
from xis.xerocraft_org_utils.xerocraftscraper import XerocraftScraper


class PaypalScraper(XerocraftScraper):

    def scrape_agreement_ids(self):

        # Attempt to log into xerocraft.org using an account that has access to treasurer tools:
        logged_in = self.login()  # type: bool
        if not logged_in:
            self.logger.error("PaypalScraper couldn't log into xerocraft.org.")
            return []

        # Get the data from the treasurer tools page:
        pw = os.environ['XEROCRAFT_WEBSITE_TREASURER_PW']
        url = "https://www.xerocraft.org/treasurer.php"
        response = self.session.post(url,data={"L": pw, "Submit": "Submit"})  # type: Response
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

