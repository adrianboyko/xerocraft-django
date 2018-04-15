
# Standard

# Third Party

# Local
from bzw_ops.etlfetchers.abstractfetcher import AbstractFetcher


# Note: This class must be named Fetcher in order for dynamic load to find it.
class Fetcher(AbstractFetcher):

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # INIT & ABSTRACT METHODS
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    def __init__(self):
        userid = input("2Checkout userid: ")
        password = input("2Checkout password: ")
        if len(userid)+len(password) == 0:
            self.skip = True
        else:
            self.skip = False

    def fetch(self):

        # max_page_num = 99
        # page_num = 1
        # while page_num <= max_page_num:
        #     opts = {'cur_page': page_num, 'pagesize': 100}
        #     page_info, sales_on_page = twocheckout.Sale.list(opts)
        #     self._process_sales(sales_on_page)
        #     max_page_num = page_info.last_page
        #     page_num += 1

        self._fetch_complete()