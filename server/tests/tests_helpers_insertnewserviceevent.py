from django.db import IntegrityError
import django
from django.test import TestCase

from server import helpers
from server.models import ServiceCategory, ServiceType, Audience, Provider, Service


class TestHelpersInsertNewServiceEvent(TestCase):

    def setUp(self):
        self.provider = Provider.objects.create(name="Unique Shop")
        self.service_category = ServiceCategory.objects.create(category="ServiceCat")
        self.service_type = ServiceType.objects.create(type="ServiceType", category=self.service_category)
        self.audience = Audience.objects.create(audience="Audience")

    def test_creates_new_service_event_happy_path(self):
        service = helpers.insert_new_service_event(category=self.service_category,
                                                   service_type=self.service_type,
                                                   provider=self.provider,
                                                   audience=self.audience,
                                                   day=0,
                                                   start_time="13:00:00",
                                                   end_time="14:00:00",
                                                   periodic=0,
                                                   note='notes'
                                                   )
        self.assertIsNotNone(service)
        self.assertIsInstance(service, Service)
        self.assertEqual(service.provider.name, "Unique Shop")
        self.assertEqual(service.category.category, "ServiceCat")
        self.assertEqual(service.type.type, "ServiceType")
        self.assertEqual(service.audience.audience, "Audience")
        self.assertEqual(service.day, 0)
        self.assertEqual(service.start_time.isoformat(), "13:00:00")
        self.assertEqual(service.end_time.isoformat(), "14:00:00")
        self.assertEqual(service.periodic, 0)
        self.assertEqual(service.note, 'notes')

    def test_unique_service_event_happy_path(self):
        service = helpers.insert_new_service_event(category=self.service_category,
                                                      service_type=self.service_type,
                                                      provider=self.provider,
                                                      audience=self.audience,
                                                      day=1,
                                                      start_time= "09:00:00",
                                                      end_time="12:00:00",
                                                      periodic=0,
                                                      note='some notes',
                                                      )
        self.assertIsNotNone(service)
        self.assertEqual(service.provider.name, "Unique Shop")
        self.assertEqual(service.category.category, "ServiceCat")
        self.assertEqual(service.type.type, "ServiceType")
        self.assertEqual(service.audience.audience, "Audience")
        self.assertEqual(service.day, 1)
        self.assertEqual(service.start_time.isoformat(), "09:00:00")
        self.assertEqual(service.end_time.isoformat(), "12:00:00")
        self.assertEqual(service.periodic, 0)
        self.assertEqual(service.note, 'some notes')

        # identical but different day
        service = helpers.insert_new_service_event(category=self.service_category,
                                                      service_type=self.service_type,
                                                      provider=self.provider,
                                                      audience=self.audience,
                                                      day=2,
                                                      start_time="09:00:00",
                                                      end_time="12:00:00",
                                                      periodic=0,
                                                      note='some notes2',
                                                      )
        self.assertIsNotNone(service)
        self.assertEqual(service.provider.name, "Unique Shop")
        self.assertEqual(service.category.category, "ServiceCat")
        self.assertEqual(service.type.type, "ServiceType")
        self.assertEqual(service.audience.audience, "Audience")
        self.assertEqual(service.day, 2)
        self.assertEqual(service.start_time.isoformat(), "09:00:00")
        self.assertEqual(service.end_time.isoformat(), "12:00:00")
        self.assertEqual(service.periodic, 0)
        self.assertEqual(service.note, 'some notes2')

        # identical but different time
        service = helpers.insert_new_service_event(category=self.service_category,
                                                      service_type=self.service_type,
                                                      provider=self.provider,
                                                      audience=self.audience,
                                                      day=2,
                                                      start_time="13:00:00",
                                                      end_time="16:00:00",
                                                      periodic=0,
                                                      note='some notes3',
                                                      )
        self.assertIsNotNone(service)
        self.assertEqual(service.provider.name, "Unique Shop")
        self.assertEqual(service.category.category, "ServiceCat")
        self.assertEqual(service.type.type, "ServiceType")
        self.assertEqual(service.audience.audience, "Audience")
        self.assertEqual(service.day, 2)
        self.assertEqual(service.start_time.isoformat(), "13:00:00")
        self.assertEqual(service.end_time.isoformat(), "16:00:00")
        self.assertEqual(service.periodic, 0)
        self.assertEqual(service.note, 'some notes3')

        # identical but different provider
        new_provider = helpers.insert_new_provider(name="New Provider")
        service = helpers.insert_new_service_event(category=self.service_category,
                                                      service_type=self.service_type,
                                                      provider=new_provider,
                                                      audience=self.audience,
                                                      day=1,
                                                      start_time="09:00:00",
                                                      end_time="12:00:00",
                                                      periodic=0,
                                                      note='some notes4',
                                                      )
        self.assertIsNotNone(service)
        self.assertEqual(service.provider.name, "New Provider")
        self.assertEqual(service.category.category, "ServiceCat")
        self.assertEqual(service.type.type, "ServiceType")
        self.assertEqual(service.audience.audience, "Audience")
        self.assertEqual(service.day, 1)
        self.assertEqual(service.start_time.isoformat(), "09:00:00")
        self.assertEqual(service.end_time.isoformat(), "12:00:00")
        self.assertEqual(service.periodic, 0)
        self.assertEqual(service.note, 'some notes4')

        # identical should not post
        starting_db_count = Service.objects.count()
        service = helpers.insert_new_service_event(category=self.service_category,
                                                      service_type=self.service_type,
                                                      provider=self.provider,
                                                      audience=self.audience,
                                                      day=1,
                                                      start_time="09:00:00",
                                                      end_time="12:00:00",
                                                      periodic=0,
                                                      note='some notes',
                                                      )
        self.assertIsNotNone(service)
        self.assertEqual(Service.objects.count(), starting_db_count) # no new object created

    def test_admin_return_flag_works(self):
        """Returns a tuple (Service obj, Boolean) if "report_status" flag activated. Flag should be True if Service obj
        created successfly, False if attempt failed because it was a duplicate."""
        starting_count = Service.objects.count()
        service, status = helpers.insert_new_service_event(category=self.service_category,
                                                   service_type=self.service_type,
                                                   provider=self.provider,
                                                   audience=self.audience,
                                                   day=0,
                                                   start_time="13:00:00",
                                                   end_time="14:00:00",
                                                   periodic=0,
                                                   note='notes',
                                                   report_status=True,
                                                   )
        self.assertIsNotNone(service)
        self.assertIsInstance(service, Service)
        self.assertEqual(service.provider.name, "Unique Shop")
        self.assertEqual(service.category.category, "ServiceCat")
        self.assertEqual(service.type.type, "ServiceType")
        self.assertEqual(service.audience.audience, "Audience")
        self.assertEqual(service.day, 0)
        self.assertEqual(service.start_time.isoformat(), "13:00:00")
        self.assertEqual(service.end_time.isoformat(), "14:00:00")
        self.assertEqual(service.periodic, 0)
        self.assertEqual(service.note, 'notes')
        self.assertEqual(status, True)
        self.assertEqual(starting_count + 1, Service.objects.count())

        intermediary_count = Service.objects.count()
        # Attempting to add duplicate
        service, status = helpers.insert_new_service_event(category=self.service_category,
                                                           service_type=self.service_type,
                                                           provider=self.provider,
                                                           audience=self.audience,
                                                           day=0,
                                                           start_time="13:00:00",
                                                           end_time="14:00:00",
                                                           periodic=0,
                                                           note='notes',
                                                           report_status=True,
                                                           )
        self.assertIsNotNone(service)
        self.assertIsInstance(service, Service)
        self.assertEqual(service.provider.name, "Unique Shop")
        self.assertEqual(service.category.category, "ServiceCat")
        self.assertEqual(service.type.type, "ServiceType")
        self.assertEqual(service.audience.audience, "Audience")
        self.assertEqual(service.day, 0)
        self.assertEqual(service.start_time.isoformat(), "13:00:00")
        self.assertEqual(service.end_time.isoformat(), "14:00:00")
        self.assertEqual(service.periodic, 0)
        self.assertEqual(service.note, 'notes')
        # all data should be correct and present, but the status will have failed and object not added to the table
        self.assertEqual(status, False)
        self.assertTrue(intermediary_count == Service.objects.count())
        self.assertTrue(starting_count + 1 == Service.objects.count())

    def test_creates_entry_when_notes_empty(self):
        service = helpers.insert_new_service_event(category=self.service_category,
                                                      service_type=self.service_type,
                                                      provider=self.provider,
                                                      audience=self.audience,
                                                      day=1,
                                                      start_time="09:00:00",
                                                      end_time="12:00:00",
                                                      periodic=0,)
        self.assertIsNotNone(service)

    def test_fail_on_invalid_foreign_key_types(self):
        """Ensure the helper catches if a string is passed instead of a Model object."""
        with self.assertRaises(TypeError):
            helpers.insert_new_service_event(
                category="Just a string",  # This should be a ServiceCategory object
                service_type=self.service_type,
                provider=self.provider,
                audience=self.audience,
                day=0,
                start_time="12:00:00",
                end_time="13:00:00",
                periodic=0,
                note="notes",
            )
        with self.assertRaises(TypeError):
            helpers.insert_new_service_event(
                category=self.service_category,
                service_type="Lunch",
                provider=self.provider,
                audience=self.audience,
                day=0,
                start_time="12:00:00",
                end_time="13:00:00",
                periodic=0,
                note='notes',
            )
        with self.assertRaises(TypeError):
            helpers.insert_new_service_event(
                category=self.service_category,
                service_type=self.service_type,
                provider="Bishop Sullivan Center",
                audience=self.audience,
                day=0,
                start_time = "12:00:00",
                end_time = "13:00:00",
                periodic = 0,
                note = 'notes',
            )
        with self.assertRaises(TypeError):
            helpers.insert_new_service_event(
                category=self.service_category,
                service_type=self.service_type,
                provider=self.provider,
                audience="Everyone",
                day=0,
                start_time="12:00:00",
                end_time="13:00:00",
                periodic=0,
                note='notes',
            )

    def test_fails_on_malformed_time_input(self):
        """Ensure the helper returns an error if time inputs are malformed."""
        with self.assertRaises(ValueError):
            helpers.insert_new_service_event(
                category=self.service_category,
                service_type=self.service_type,
                provider=self.provider,
                audience=self.audience,
                day=0,
                start_time="12AM",
                end_time="13:00:00",
                periodic=0,
                note='notes',
            )
        with self.assertRaises(ValueError):
            helpers.insert_new_service_event(
                category=self.service_category,
                service_type=self.service_type,
                provider=self.provider,
                audience=self.audience,
                day=0,
                start_time="12:00:00",
                end_time="1:30 PM",
                periodic=0,
                note='notes',
            )




