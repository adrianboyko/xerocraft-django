import abc


class AbstractFetcher(object):  # The "ET" in "ETL"

    __metalass__ = abc.ABCMeta

    @abc.abstractmethod
    def generate_paid_memberships(self):
        """Yields an unsaved PaidMembership instance"""
        return
