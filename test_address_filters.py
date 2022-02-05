import unittest
from address_filters import AddressFilters


class TestAddressFilters(unittest.TestCase):

    addresses_under_test = [
        "president@whitehouse.gov",
        "first.lady@whitehouse.gov",
        "darth.vadar@deathstar.com",
        "t.stark@tstarindustries.com",
    ]

    filter_out_addresses = ["first.lady@whitehouse.gov", "darth.vadar@deathstar.com"]
    after_filter_addresses = ["president@whitehouse.gov", "t.stark@tstarindustries.com"]

    filter_out_domains = ["whitehouse.gov"]
    after_filter_domains = ["darth.vadar@deathstar.com", "t.stark@tstarindustries.com"]

    """ make sure filter passes back everything if no rules set"""

    def test_returns_all(self):
        filters = AddressFilters(ignore_addresses=[], ignore_domains=[])
        self.assertEqual(
            self.addresses_under_test,
            filters.recipients_filter(self.addresses_under_test),
        )

    def test_returns_filter_addresses(self):
        filters = AddressFilters(
            ignore_addresses=self.filter_out_addresses, ignore_domains=[]
        )
        self.assertEqual(
            self.after_filter_addresses,
            filters.recipients_filter(self.addresses_under_test),
        )

    def test_returns_filter_domains(self):
        filters = AddressFilters(
            ignore_addresses=[], ignore_domains=self.filter_out_domains
        )
        self.assertEqual(
            self.after_filter_domains,
            filters.recipients_filter(self.addresses_under_test),
        )


if __name__ == "__main__":
    unittest.main()
