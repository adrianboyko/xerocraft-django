
# Standard
import logging
import os
from datetime import datetime
from hashlib import sha512

# Third party
from django.conf import settings

# Local


__author__ = 'adrian'


class XerocraftScraper(object):

    SERVER_DEV = "https://www.xerocraft.org/kfritz/"
    SERVER_PROD = "https://www.xerocraft.org/"

    def __init__(self, server_override=None):
        super().__init__()
        self.logger = logging.getLogger("xis")
        if server_override is not None:
            self.server = server_override
        else:
            self.server = XerocraftScraper.SERVER_DEV if settings.ISDEVHOST else XerocraftScraper.SERVER_PROD

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

    @staticmethod
    def djangofy_username(username):
        username = username.strip()  # Kyle has verified that xerocraft.org database has some untrimmed usernames.
        newname = ""
        for c in username:
            if c.isalnum() or c in "_@+.-":
                newname += c
            else:
                newname += "_"
        return newname

    @staticmethod
    def get_token() -> str:

        if not 'XCORG_SECRET_STRING' in os.environ:
            raise RuntimeError("XCORG_SECRET_STRING must be set in environment.")
        if not 'XCORG_SECRET_DATEFMT' in os.environ:
            raise RuntimeError("XCORG_SECRET_DATEFMT must be set in environment.")

        initstr = os.environ['XCORG_SECRET_STRING']
        datefmt = os.environ['XCORG_SECRET_DATEFMT']
        datestr = datetime.now().strftime(datefmt)
        codestr = datestr + initstr + datestr
        token = sha512(codestr.encode('ascii')).hexdigest()
        return token
