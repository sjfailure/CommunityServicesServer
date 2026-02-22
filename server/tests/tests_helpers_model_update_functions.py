from unittest.mock import patch
import datetime
import logging

from django.test import TestCase
from django.utils import timezone

from server.models import (Provider, Service, Event, ServiceType,
                           ServiceCategory, Audience, Day)
from server import helpers


class TestHelpersModelUpdateFunctions(TestCase):
    """
    Test Suite for server.helpers.purge_old_events(),
    server.helpers.sync_service_definitions(), and
    server.helpers.update_event_table().
    """

    def setUp(self):
        # 1. Create basic requirements
        self.provider = Provider.objects.create(
            name="Test Provider",
            address="123 Test St")
        self.category = ServiceCategory.objects.create(
            category="Health")
        self.category2 = ServiceCategory.objects.create(
            category='Second Category')
        self.stype = ServiceType.objects.create(type="Showers",
                                                category=self.category)
        self.stype2 = ServiceType.objects.create(
            type='Other Health Type', category=self.category)
        self.stype3 = ServiceType.objects.create(
            type='Non Health Type', category=self.category2)
        self.audience = Audience.objects.create(audience="Everyone")
        self.audience2 = Audience.objects.create(
            audience="Specialized Audience")

        # 2. Ensure Day table is populated (0-6)
        # for i in range(7):
        #     Day.objects.get_or_create(id=i)

    def test_purge_old_events(self):
        """Ensure events that have ended are deleted."""
        service = Service.objects.create(provider=self.provider)

        # Event in the past
        past_time = timezone.now() - datetime.timedelta(hours=5)
        Event.objects.create(
            service_id=service,
            date=past_time - datetime.timedelta(hours=1), end=past_time)

        # Event in the future
        future_time = timezone.now() + datetime.timedelta(hours=5)
        Event.objects.create(
            service_id=service,
            date=future_time,
            end=future_time + datetime.timedelta(hours=1))

        helpers.purge_old_events()

        self.assertEqual(Event.objects.count(), 1)
        self.assertGreater(Event.objects.first().end, timezone.now())

    @patch('server.helpers.event_info')
    def test_sync_service_definitions_handles_m2m_days(self, mock_info):
        """
        Verify services and M2M Service.day relations are
        created from source data.
        """
        # Mocking the service_list data structure
        mock_info.service_list = {
            'test_service': {
                'provider': 'Test Provider',
                'start_time': datetime.time(10, 0),
                'end_time': datetime.time(11, 0),
                'day': [0, 2],  # Mon, Wed
                'service_type': 'Showers',
                'audience': 'Everyone',
                'note': 'Test Note'
            }
        }

        helpers.sync_service_definitions()

        # Assertions
        service = Service.objects.get(note='Test Note')
        self.assertEqual(service.provider.name, "Test Provider")
        self.assertEqual(service.day.count(), 2)
        self.assertEqual(service.type.first().type, "Showers")
        self.assertEqual(service.audience.first().audience,
                         "Everyone")

    @patch('server.helpers.event_info')
    def test_sync_service_definitions_handles_single_day(self,
                                                         mock_info):
        """
        Verify services and non-M2M Service.day relations are
        created from source data.
        """
        # Mocking the service_list data structure
        mock_info.service_list = {
            'test_service': {
                'provider': 'Test Provider',
                'start_time': datetime.time(10, 0),
                'end_time': datetime.time(11, 0),
                'day': 0,  # Mon
                'service_type': 'Showers',
                'audience': 'Everyone',
                'note': 'Test Note'
            }
        }
        logging.debug(f'Provider list is '
                      f'{Provider.objects.first().name}')
        self.assertTrue(Provider.objects.count() > 0)

        helpers.sync_service_definitions()

        # Assertions
        service = Service.objects.get(note='Test Note')
        self.assertEqual(service.provider.name,
                         "Test Provider")
        self.assertEqual(service.day.count(), 1)
        self.assertEqual(service.type.first().type, "Showers")
        self.assertEqual(service.audience.first().audience,
                         "Everyone")

    @patch('server.helpers.event_info')
    def test_sync_service_definitions_handles_m2m_audiences(self,
                                                            mock_info):

        """
        Verify services and M2M Service.audience relations
        are created from source data.
        """
        # Mocking the service_list data structure
        mock_info.service_list = {
            'test_service': {
                'provider': 'Test Provider',
                'start_time': datetime.time(10, 0),
                'end_time': datetime.time(11, 0),
                'day': [0, 2],  # Mon, Wed
                'service_type': 'Showers',
                'audience': ['Everyone', "Specialized Audience"],
                'note': 'Test Note'
            }
        }

        helpers.sync_service_definitions()

        # Assertions
        service = Service.objects.get(note='Test Note')
        self.assertEqual(service.provider.name, "Test Provider")
        self.assertEqual(service.day.count(), 2)
        self.assertEqual(service.type.first().type, "Showers")
        self.assertEqual(service.audience.count(), 2)
        self.assertIn(self.audience2, service.audience.all())
        self.assertIn(self.audience, service.audience.all())

    @patch('server.helpers.event_info')
    def test_sync_service_definitions_handles_m2m_types(self,
                                                        mock_info):

        """
        Verify services and M2M Service.type relations are created
        from source data.
        """
        # Mocking the service_list data structure
        mock_info.service_list = {
            'test_service': {
                'provider': 'Test Provider',
                'start_time': datetime.time(10, 0),
                'end_time': datetime.time(11, 0),
                'day': [0, 2],  # Mon, Wed
                'service_type': ['Showers', 'Other Health Type'],
                'audience': 'Everyone',
                'note': 'Test Note'
            }
        }

        helpers.sync_service_definitions()

        # Assertions
        service = Service.objects.get(note='Test Note')
        self.assertEqual(service.provider.name, "Test Provider")
        self.assertEqual(service.day.count(), 2)
        self.assertEqual(service.type.count(), 2)
        self.assertIn("Showers", [x.type for x in
                                  service.type.all()])
        self.assertIn("Other Health Type", [x.type for x in
                                            service.type.all()])
        self.assertEqual(service.audience.count(), 1)
        self.assertNotIn("Specialized Audience",
                         service.audience.all())
        self.assertIn(self.audience, service.audience.all())

    @patch('server.helpers.event_info')
    def test_sync_service_definitions_handles_m2m_types_different_categories(
            self, mock_info):
        """
        Verify services and M2M Service.type relations (with
        different categories) are created from source data.
        """
        # Mocking the service_list data structure
        mock_info.service_list = {
            'test_service': {
                'provider': 'Test Provider',
                'start_time': datetime.time(10, 0),
                'end_time': datetime.time(11, 0),
                'day': [0, 2],  # Mon, Wed
                'service_type': ['Showers', 'Non Health Type'],
                'audience': 'Everyone',
                'note': 'Test Note'
            }
        }

        helpers.sync_service_definitions()

        # Assertions
        service = Service.objects.get(note='Test Note')
        self.assertEqual(service.provider.name, "Test Provider")
        self.assertEqual(service.day.count(), 2)
        self.assertEqual(service.type.count(), 2)
        self.assertIn("Showers", [x.type for x in
                                  service.type.all()])
        self.assertIn("Non Health Type", [x.type for x in
                                          service.type.all()])
        self.assertEqual(len({x.category for x in
                                  service.type.all()}), 2)
        self.assertEqual(service.audience.count(), 1)
        self.assertNotIn(self.audience2, service.audience.all())
        self.assertIn(self.audience, service.audience.all())

    @patch('server.helpers.sync_service_definitions')
    def test_update_event_table_generates_correct_dates(
            self, mock_sync):
        # 1. Create your service manually (which you already do)
        service = Service.objects.create(
            provider=self.provider,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0)
        )
        service.day.add(Day.objects.get(id=0))

        # 2. Run the table update
        # The code will call the mock_sync (which does nothing) and
        # then proceed straight to the date generation logic.
        helpers.update_event_table()

        events = Event.objects.filter(service_id=service)
        self.assertGreater(events.count(), 0)
        for event in events:
            self.assertEqual(event.date.weekday(), 0)
