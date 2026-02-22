"""
Contains CLI functions to pre-populate the Provider, Cateogory, and
Types tables with hard-coded data. Accessed via
"manage.py populate_data".
"""

from django.core.management.base import BaseCommand
from server.helpers import sync_service_definitions

import server


def populate_providers():
    # Provider = apps.get_model('server', 'Provider')
    provider_data = server.event_info.all_providers
    for provider, info in provider_data.items():
        server.helpers.insert_new_provider(
            name=provider,
            address=info[0],
            phone=info[1],
            email=info[2]
        )

def populate_categories_types():
    # Category = apps.get_model('server', 'ServiceCategory')
    # Types = apps.get_model('server', 'ServiceType')
    category_data = server.event_info.all_categories_and_types
    for category in category_data:
        category_instance = server.helpers.insert_new_service_category(category)
        type_data = category_data[category]
        for service_type in type_data:
            server.helpers.insert_new_service_type(service_type, category_instance)

def populate_audience():
    # Audience = apps.get_model('server', 'Audience')
    for audience in server.event_info.all_audiences:
        server.helpers.insert_new_audience(audience)


class Command(BaseCommand):
    help = 'Populates the database with real-world service definitions'

    def handle(self, *args, **options):
        self.stdout.write("Syncing services...")
        populate_providers()
        populate_audience()
        populate_categories_types()
        sync_service_definitions()
        self.stdout.write(self.style.SUCCESS("Successfully synced 27 services!"))
