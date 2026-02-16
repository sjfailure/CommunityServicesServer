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

    def test_returns_report_status(self):
        """
        Ensure the report_status flag returns when requested,
        reports when a record is created (True) or not (False).
        """
        current_db_count = Provider.objects.count()
        provider, status = helpers.insert_new_provider(name="Provider A", report_status=True)
        self.assertEqual(Provider.objects.count(), current_db_count + 1)
        self.assertTrue(status)
        provider2, status2 = helpers.insert_new_provider(name="Provider B", report_status=True)
        self.assertEqual(Provider.objects.count(), current_db_count + 2)
        self.assertTrue(status2)
        # Attempt Duplicate entry, should not create
        provider3, status3 = helpers.insert_new_provider(name="Provider A", report_status=True)
        self.assertEqual(Provider.objects.count(), current_db_count + 2) # Same as before attempt
        self.assertEqual(Provider.objects.get(name="Provider A"), provider3) # Returns conflicting record
        self.assertFalse(status3) # flag comes back false

    # --- NEGATIVE & EDGE CASES ---

    def test_fails_on_wrong_type(self):
        """If we provide an integer instead of a string, it should raise TypeError."""
        with self.assertRaises(TypeError):
            helpers.insert_new_provider(name=12345)

    def test_handles_explicit_none_for_required_field(self):
        """
        Prevent None from being used as Provider name.
        """
        with self.assertRaises(ValueError):
            result = helpers.insert_new_provider(name=None)


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

    def test_unique_together_returns_existing_instead_of_none(self):
        """
        Tests that attempting to create a duplicate name/address pair
        returns the EXISTING provider rather than None.
        """
        shared_name = "Central Clinic"
        shared_address = "123 Main St"

        # 1. Create the first entry
        first_result = helpers.insert_new_provider(name=shared_name, address=shared_address)
        initial_count = Provider.objects.count()

        # 2. Attempt duplicate
        second_result = helpers.insert_new_provider(name=shared_name, address=shared_address)

        # 3. Assertions
        self.assertIsNotNone(second_result)
        self.assertEqual(first_result.id, second_result.id)  # They should be the same object
        self.assertEqual(Provider.objects.count(), initial_count)  # No new record created

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
