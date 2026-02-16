import unittest

from django.db import IntegrityError
import django

from server import helpers
from server.models import ServiceCategory, ServiceType, Audience


class TestHelpersInsertNewType(django.test.TestCase):

    def setUp(self):
        # We need a valid Category for almost every test
        self.category = ServiceCategory.objects.create(category="Health")

    def test_creates_new_service_type_successfully(self):
        """Standard case: Valid category and new type name."""
        type_name = "Primary Care"

        result = helpers.insert_new_service_type(type_name, self.category)

        self.assertEqual(ServiceType.objects.count(), 1)
        self.assertEqual(result.type, type_name)
        self.assertEqual(result.category, self.category)

    def test_fails_on_invalid_category_type(self):
        """Ensure it raises TypeError if we pass a string instead of a model instance."""
        with self.assertRaises(TypeError):
            # Passing a string "Health" instead of the self.category object
            helpers.insert_new_service_type("Dental", "Health")

    def test_idempotency_same_category(self):
        """Ensure it returns the existing type if name and category match."""
        type_name = "Counseling"
        # First creation
        helpers.insert_new_service_type(type_name, self.category)

        # Second creation attempt
        result = helpers.insert_new_service_type(type_name, self.category)

        self.assertEqual(ServiceType.objects.count(), 1)
        self.assertIsInstance(result, ServiceType)

    # NO LONGER VALID, SAME NAME, DIFFERENT CATEGORY IS ALLOWED
    # def test_same_name_different_category(self):
    #     """
    #     Unique constraint on ServiceType.type prevents multiple services of same type in separate categories.
    #     """
    #     other_cat = ServiceCategory.objects.create(category="Education")
    #     type_name = "Workshops"
    #
    #     helpers.insert_new_service_type(type_name, self.category)
    #     with self.assertRaises(IntegrityError):
    #         helpers.insert_new_service_type(type_name, other_cat)
    #
    #     self.assertEqual(ServiceType.objects.count(), 1)

class TestHelpersRetrieveType(django.test.TestCase):

    def setUp(self):
        # Create foundational data for retrieval tests
        self.cat = ServiceCategory.objects.create(category="Food")
        self.stype = ServiceType.objects.create(type="Pantry", category=self.cat)
        self.aud = Audience.objects.create(audience="Families")

    def test_retrieve_service_type_success(self):
        # Note: Ensure the argument name matches your helper's 'type'
        found = helpers.retrieve_service_type("Pantry")
        self.assertEqual(found.id, self.stype.id)