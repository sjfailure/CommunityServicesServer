import unittest

from django.db import IntegrityError
import django

from server import helpers
from server.models import ServiceCategory, ServiceType, Audience


class TestHelpersInsertNewCategory(django.test.TestCase):

    def test_creates_new_category_if_missing(self):
        """Standard case: Category doesn't exist yet."""
        name = "Healthcare"

        result = helpers.insert_new_service_category(name)

        self.assertEqual(ServiceCategory.objects.count(), 1)
        self.assertEqual(result.category, name)
        self.assertIsInstance(result, ServiceCategory)

    def test_retrieves_existing_category_without_duplicating(self):
        """Ensure it doesn't create a second record if name matches."""
        name = "Youth Services"
        # Pre-seed the database
        ServiceCategory.objects.create(category=name)
        initial_count = ServiceCategory.objects.count()

        # Action
        result = helpers.insert_new_service_category(name)

        # Assertions
        self.assertEqual(ServiceCategory.objects.count(), initial_count)  # Still 1
        self.assertEqual(result.category, name)

    def test_handles_empty_input(self):
        """Edge case: What if the category name is an empty string?"""
        # This depends on if your model allows blank strings
        result = helpers.insert_new_service_category("")
        self.assertEqual(result.category, "")

class TestHelpersRetrieveCatergory(django.test.TestCase):

    def setUp(self):
        # Create foundational data for retrieval tests
        self.cat = ServiceCategory.objects.create(category="Food")
        self.stype = ServiceType.objects.create(type="Pantry", category=self.cat)
        self.aud = Audience.objects.create(audience="Families")

    def test_retrieve_service_category_success(self):
        found = helpers.retrieve_service_category("Food")
        self.assertEqual(found.id, self.cat.id)

    def test_retrieve_service_category_none(self):
        self.assertIsNone(helpers.retrieve_service_category("Non-Existent"))