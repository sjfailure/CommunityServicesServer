import unittest

from django.db import IntegrityError
import django

from server import helpers
from server.models import ServiceCategory, ServiceType, Audience

class TestHelpersInsertNewAudienceAndRetrieveAudience(django.test.TestCase):

    def setUp(self):
        # Create foundational data for retrieval tests
        self.cat = ServiceCategory.objects.create(category="Food")
        self.stype = ServiceType.objects.create(type="Pantry", category=self.cat)
        self.aud = Audience.objects.create(audience="Families")

    def test_insert_new_audience_idempotency(self):
        """Proof that calling it twice doesn't duplicate the record."""
        helpers.insert_new_audience("Seniors")
        helpers.insert_new_audience("Seniors")
        self.assertEqual(Audience.objects.filter(audience="Seniors").count(), 1)

    def test_retrieve_audience_success(self):
        found = helpers.retrieve_audience("Families")
        self.assertEqual(found.id, self.aud.id)