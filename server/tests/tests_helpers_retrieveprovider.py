import django

from server import helpers
from server.models import Provider


class TestHelpersRetrieveProvider(django.test.TestCase):
    """
    Test Suite for helpers.retrieve_provider().
    """
    def setUp(self):
        # Create a "Gold Standard" record to find later
        self.provider = Provider.objects.create(
            name="Searchable Clinic", address="123 Discovery Way")

    def test_retrieve_provider_finds_correct_instance(self):
        """Proof of concept: Can we find the provider by name?"""
        found = helpers.retrieve_provider(name="Searchable Clinic")
        self.assertEqual(found.id, self.provider.id)

    def test_retrieve_provider_returns_none_when_not_found(self):
        """
        Negative test: Ensure it doesn't crash if the provider 
        doesn't exist.
        """
        found = helpers.retrieve_provider(name="Non-Existent")
        self.assertIsNone(found)


class TestRetrieveProviderAmbiguity(django.test.TestCase):
    """
    Specific tests for handling multiple providers with the same 
    name.
    """

    def setUp(self):
        # Setup two providers with the exact same name but different addresses
        self.name = "Community Health"
        self.p1 = Provider.objects.create(
            name=self.name, address="100 North St")
        self.p2 = Provider.objects.create(
            name=self.name, address="200 South St")

    def test_retrieve_disambiguates_with_correct_address(self):
        """
        Should return the specific record matching both name and 
        address.
        """
        found = helpers.retrieve_provider(
            name=self.name, address="200 South St")
        self.assertEqual(found.id, self.p2.id)
        self.assertEqual(found.address, "200 South St")

    def test_retrieve_raises_lookup_error_when_ambiguous(self):
        """
        Should raise LookupError if name is non-unique and no 
        address is given.
        """
        # This matches the 'except MultipleObjectsReturned' logic in 
        # your helper
        with self.assertRaises(LookupError) as cm:
            helpers.retrieve_provider(name=self.name)

        self.assertIn("Multiple providers named", str(cm.exception))

    def test_retrieve_returns_none_if_address_mismatch(self):
        """
        Should return None if the name exists twice, but the 
        address matches neither.
        """
        found = helpers.retrieve_provider(
            name=self.name, address="999 Wrong Way")
        self.assertIsNone(found)

    def test_retrieve_by_unique_name_ignores_unnecessary_address(self):
        """
        If a name is unique, it should return the provider even if 
        address isn't passed.
        """
        unique_p = Provider.objects.create(
            name="Unique Shop", address="1 Main St")
        found = helpers.retrieve_provider(name="Unique Shop")
        self.assertEqual(found.id, unique_p.id)
