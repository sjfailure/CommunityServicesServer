import logging

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
        self.assertIn(self.service_category, service.category.all())
        self.assertIn(self.service_type, service.type.all())
        self.assertIn(self.audience, service.audience.all())
        self.assertIn(helpers.retrieve_day(0), service.day.all())
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
        self.assertIn(self.service_category, service.category.all())
        self.assertIn(self.service_type, service.type.all())
        self.assertIn(self.audience, service.audience.all())
        self.assertIn(helpers.retrieve_day(1), service.day.all())
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
        self.assertIn(self.service_category, service.category.all())
        self.assertIn(self.service_type, service.type.all())
        self.assertIn(self.audience, service.audience.all())
        self.assertIn(helpers.retrieve_day(2), service.day.all())
        self.assertEqual(service.start_time.isoformat(), "09:00:00")
        self.assertEqual(service.end_time.isoformat(), "12:00:00")
        self.assertEqual(service.periodic, 0)
        self.assertEqual(service.note, 'some notes')

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
        self.assertIn(self.service_category, service.category.all())
        self.assertIn(self.service_type, service.type.all())
        self.assertIn(self.audience, service.audience.all())
        self.assertIn(helpers.retrieve_day(2), service.day.all())
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
        self.assertIn(self.service_category, service.category.all())
        self.assertIn(self.service_type, service.type.all())
        self.assertIn(self.audience, service.audience.all())
        self.assertIn(helpers.retrieve_day(1), service.day.all())
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
        created successfully, False if attempt failed because it was a duplicate."""
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
        self.assertIn(self.service_category, service.category.all())
        self.assertIn(self.service_type, service.type.all())
        self.assertIn(self.audience, service.audience.all())
        self.assertIn(helpers.retrieve_day(0), service.day.all())
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
        self.assertIn(self.service_category, service.category.all())
        self.assertIn(self.service_type, service.type.all())
        self.assertIn(self.audience, service.audience.all())
        self.assertIn(helpers.retrieve_day(0), service.day.all())
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
        with self.assertRaises(ValueError):
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
        with self.assertRaises(ValueError):
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
        with self.assertRaises(ValueError):
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
        with self.assertRaises(ValueError):
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


    def test_create_with_multiple_categories_and_audiences(self):
        """Verify a single service can be tagged with multiple M2M objects during creation."""
        cat2 = ServiceCategory.objects.create(category="Financial Counseling")
        audi2 = Audience.objects.create(audience="Veterans")

        service = helpers.insert_new_service_event(
            category=[self.service_category, cat2],  # Passing a list
            service_type=self.service_type,
            provider=self.provider,
            audience=[self.audience, audi2],  # Passing a list
            day=0,
            start_time="10:00:00",
            end_time="11:00:00",
            periodic=0
        )

        # Verify counts
        self.assertEqual(service.category.count(), 2)
        self.assertEqual(service.audience.count(), 2)

        # Verify specific members
        self.assertIn(cat2, service.category.all())
        self.assertIn(audi2, service.audience.all())


    def test_update_existing_service_adds_new_category(self):
        """
        Verify that calling the helper for an existing time-slot adds new M2M
        relationships rather than creating a duplicate Service record.
        """
        # 1. Create initial service
        helpers.insert_new_service_event(
            category=self.service_category,
            service_type=self.service_type,
            provider=self.provider,
            audience=self.audience,
            day=4,
            start_time="14:00:00",
            end_time="15:00:00",
            periodic=0
        )
        starting_count = Service.objects.count()

        # 2. Call again with a NEW category for the SAME provider/time
        new_cat = ServiceCategory.objects.create(category="New Add-on Service")
        service, created = helpers.insert_new_service_event(
            category=new_cat,
            service_type=self.service_type,
            provider=self.provider,
            audience=self.audience,
            day=4,
            start_time="14:00:00",
            end_time="15:00:00",
            periodic=0,
            report_status=True
        )

        self.assertFalse(created)  # Should have found the existing record
        self.assertEqual(Service.objects.count(), starting_count)  # No new DB row

        # 3. Verify the existing record now has BOTH categories
        self.assertEqual(service.category.count(), 2)
        self.assertIn(self.service_category, service.category.all())
        self.assertIn(new_cat, service.category.all())


    def test_m2m_idempotency(self):
        """Verify that adding the same category multiple times doesn't create duplicate links."""
        service = helpers.insert_new_service_event(
            category=[self.service_category, self.service_category, self.service_category],
            service_type=self.service_type,
            provider=self.provider,
            audience=self.audience,
            day=0,
            start_time="08:00:00",
            end_time="09:00:00",
            periodic=0
        )
        # Django's M2M .add() should filter out duplicates automatically
        self.assertEqual(service.category.count(), 1)

    def test_create_service_with_multiple_days_list(self):
        """Verify passing a list of days tags a single service with all of them."""
        days_to_add = [helpers.retrieve_day(0), helpers.retrieve_day(2), helpers.retrieve_day(4)]

        service = helpers.insert_new_service_event(
            category=self.service_category,
            service_type=self.service_type,
            provider=self.provider,
            audience=self.audience,
            day=days_to_add,  # Passing the list
            start_time="10:00:00",
            end_time="11:00:00",
            periodic=0
        )

        self.assertEqual(service.day.count(), 3)
        for d in days_to_add:
            self.assertIn(d, service.day.all())

    def test_adding_new_day_to_existing_service_consolidates(self):
        """Verify that calling the helper with a new day adds it to the existing Service object."""
        # 1. Create for Monday
        helpers.insert_new_service_event(
            category=self.service_category,
            service_type=self.service_type,
            provider=self.provider,
            audience=self.audience,
            day=0,
            start_time="09:00:00",
            end_time="10:00:00",
            periodic=0
        )
        initial_count = Service.objects.count()

        # 2. Call again for Wednesday (Same time/provider)
        service, created = helpers.insert_new_service_event(
            category=self.service_category,
            service_type=self.service_type,
            provider=self.provider,
            audience=self.audience,
            day=2,
            start_time="09:00:00",
            end_time="10:00:00",
            periodic=0,
            report_status=True
        )

        self.assertFalse(created)  # Should NOT create a new row
        self.assertEqual(Service.objects.count(), initial_count)
        self.assertEqual(service.day.count(), 2)  # Should now have Monday AND Wednesday
        self.assertIn(helpers.retrieve_day(0), service.day.all())
        self.assertIn(helpers.retrieve_day(2), service.day.all())

    def test_day_idempotency(self):
        """Verify that adding the same day twice doesn't create duplicate M2M links."""
        service = helpers.insert_new_service_event(
            category=self.service_category,
            service_type=self.service_type,
            provider=self.provider,
            audience=self.audience,
            day=[0, 0, 0],  # Spamming Monday
            start_time="15:00:00",
            end_time="16:00:00",
            periodic=0
        )
        self.assertEqual(service.day.count(), 1)
