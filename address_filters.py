"""
Support filtering of a list used to ignore trusted adress and domains

Can filter out certain addresses or domains.
Address and Domain filters remove address or addresses in specific domains.
Address and Domain filters must be exact matches. 

"""
import logging


class AddressFilters:
    def __init__(self, ignore_addresses, ignore_domains):
        self.logger = logging.getLogger(__name__)
        self.ignore_addresses = ignore_addresses
        self.ignore_domains = ignore_domains

    def recipients_filter(self, recipients):
        """Return a list of the addresses that meat some criteria not yet mplemented"""
        # filter out trusted addresses
        filtered_by_addresses = [
            x for x in recipients if x not in self.ignore_addresses
        ]
        # filter out trusted domains - full domains
        filtered = [
            x
            for x in filtered_by_addresses
            if x[x.index("@") + 1 :] not in self.ignore_domains
        ]
        return filtered
