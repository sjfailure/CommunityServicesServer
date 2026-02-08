import unittest

from django.db import IntegrityError
import django

from server import helpers
from server.models import Provider


class TestHelpersInsertNewProvider(django.test.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_provider_with_all_fields(self):
        """Ensure a provider is saved correctly when all data is provided."""
        # 1. Action
        current_db_count = Provider.objects.count()
        provider = helpers.insert_new_provider(
            name="Health First",
            address="123 Medical Way",
            phone="555-0199",
            email="contact@healthfirst.org"
        )

        # 2. Assertions (Checking the DB)

        self.assertEqual(Provider.objects.count(), current_db_count + 1)
        saved_provider = Provider.objects.get(id=provider.id)

        self.assertEqual(saved_provider.name, "Health First")
        self.assertEqual(saved_provider.address, "123 Medical Way")
        self.assertEqual(saved_provider.phone, "555-0199")
        self.assertEqual(saved_provider.email, "contact@healthfirst.org")

    def test_create_provider_minimal_data(self):
        """Ensure the helper works with only the name (others are optional)."""
        provider = helpers.insert_new_provider(name="Minimalist Clinic")

        self.assertEqual(provider.name, "Minimalist Clinic")
        self.assertIsNone(provider.address)
        self.assertIsNone(provider.email)

    def test_create_provider_returns_instance(self):
        """The function should return the created object instance."""
        provider = helpers.insert_new_provider(name="Return Test")
        self.assertIsInstance(provider, Provider)

    def test_create_multiple_providers(self):
        """Ensure we can call the helper multiple times without conflict."""
        current_db_count = Provider.objects.count()
        helpers.insert_new_provider(name="Provider A")
        helpers.insert_new_provider(name="Provider B")
        self.assertEqual(Provider.objects.count(), current_db_count + 2)

    # --- NEGATIVE & EDGE CASES ---

    def test_provider_uses_default_name_when_omitted(self):
        """If we don't provide a name, it should default to 'No Provider'."""
        # We call it with NO name
        provider = helpers.insert_new_provider(address="123 Lane")

        self.assertEqual(provider.name, "No Provider")
        self.assertEqual(provider.address, "123 Lane")

    def test_fails_on_wrong_type(self):
        """If we provide an integer instead of a string, it should raise TypeError."""
        with self.assertRaises(TypeError):
            helpers.insert_new_provider(name=12345)

    def test_handles_explicit_none_for_required_field(self):
        """
        Your model says name has a default, but if we explicitly pass None,
        the DB might complain because null=False is the default for TextField.
        """
        result = helpers.insert_new_provider(name=None)
        self.assertIsNone(result)

    def test_large_input_handling(self):
        """TextFields should handle very large strings, but we should verify."""
        huge_name = "A" * 10000
        p = helpers.insert_new_provider(name=huge_name)
        self.assertEqual(len(p.name), 10000)

    def test_type_safety_handling(self):
        """
        What happens if a dictionary or list is passed instead of a string?
        Depending on your helper logic, you might want it to fail early.
        """
        with self.assertRaises(Exception):
            # This is a 'defensive' test; you might want to add logic
            # in the helper to catch this.
            helpers.insert_new_provider(name={"not": "a string"})

    def test_unique_together_name_and_address_fails_safely(self):
        """
        Tests that attempting to create a duplicate name/address pair
        returns None rather than crashing the system.
        """
        shared_name = "Central Clinic"
        shared_address = "123 Main St"

        # 1. Create the first entry
        first_result = helpers.insert_new_provider(name=shared_name, address=shared_address)
        self.assertIsNotNone(first_result)
        initial_count = Provider.objects.count()

        # 2. Attempt duplicate - Should return None, NOT raise IntegrityError
        second_result = helpers.insert_new_provider(name=shared_name, address=shared_address)

        self.assertIsNone(second_result)
        self.assertEqual(Provider.objects.count(), initial_count)

    def test_partial_match_is_allowed(self):
        """
        Ensures that if only one field matches, it is NOT a violation.
        """
        helpers.insert_new_provider(name="Central Clinic", address="123 Main St")

        # This should succeed because the address is different
        try:
            helpers.insert_new_provider(name="Central Clinic", address="456 Oak Ave")
        except IntegrityError:
            self.fail("IntegrityError raised for different addresses!")
