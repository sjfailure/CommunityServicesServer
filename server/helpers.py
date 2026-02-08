import datetime
import re
from datetime import time

import pytz
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError, transaction

from server.models import Event, Provider, ServiceCategory, ServiceType, Audience, Service


def get_all_entries():
    pass

def get_service_type(event_query_set_obj):
    return event_query_set_obj.service_id.type.type

def get_service_category(event_query_set_obj):
    return event_query_set_obj.service_id.category.category

def get_provider_name(event_query_set_obj):
    return event_query_set_obj.service_id.provider.name

def get_service_location(event_query_set_obj):
    return event_query_set_obj.service_id.provider.address

def get_provider_phone_number(event_query_set_obj):
    return event_query_set_obj.service_id.provider.phone

def get_service_target_audience(event_query_set_obj):
    return event_query_set_obj.service_id.audience.audience

def event_data_packer(entry):
    return {
        'provider_name': get_provider_name(entry),
        'service_category': get_service_category(entry),
        'service_type': get_service_type(entry),
        'address': get_service_location(entry),
        'phone': get_provider_phone_number(entry),
        'email': entry.service_id.provider.email,
        'start_time': entry.date.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': entry.end.strftime('%Y-%m-%d %H:%M:%S'),
        'audience': get_service_target_audience(entry),
        'notes': entry.service_id.note,
    }

def pull_event_detail_view(event_id):
    event = Event.objects.get(id=event_id)
    collected_data = {
        'id': event_id,
        'start': event.date,
        'end': event.end,
        'service_id': event.service_id.id,
        'category': event.service_id.category.category,
        'type': event.service_id.type.type,
        'provider': event.service_id.provider.name,
        'address': event.service_id.provider.address,
        'phone': event.service_id.provider.phone,
        'email_address': event.service_id.provider.email,
        'note': event.service_id.note,
        'audience': event.service_id.audience.audience,
    }
    return collected_data

def insert_new_service_event(category, service_type, day, start_time, end_time, periodic, audience, provider, note=None, report_status=False):
    if not isinstance(category, ServiceCategory):
        raise TypeError(f"Field '{category}' must be ServiceCategory.")
    if not isinstance(service_type, ServiceType):
        raise TypeError(f"Field '{service_type}' must be ServiceType.")
    if not isinstance(audience, Audience):
        raise TypeError(f"Field '{audience}' must be Audience.")
    if not isinstance(provider, Provider):
        raise TypeError(f"Field '{provider}' must be Provider.")
    if not isinstance(day, int):
        raise TypeError(f"Field '{day}' must be int.")
    if day < 0 or day > 6:
        raise ValueError(f"Field '{day}' must be between 0 and 6.")
    if not isinstance(start_time, str):
        raise TypeError(f"Field '{start_time}' must be a str in 'HH:mm:ss' format.")
    time_pattern = r"^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$"
    if not re.match(time_pattern, start_time):
        raise ValueError(f"Field '{start_time}' must be in 'HH:mm:ss' format.")
    if not isinstance(end_time, str):
        raise TypeError(f"Field '{end_time}' must be a str in 'HH:mm:ss' format.")
    if not re.match(time_pattern, end_time):
        raise ValueError(f"Field '{end_time}' must be in 'HH:mm:ss' format.")
    if not isinstance(periodic, int):
        raise TypeError(f"Field '{periodic}' must be int.")
    if not isinstance(note, str) and note is not None:
        raise TypeError(f"Field '{note}' must be str in 'Note' format.")
    time_zone = pytz.timezone("America/Chicago")
    h1, m1, s1 = start_time.split(":")
    h2, m2, s2 = end_time.split(":")
    start = datetime.time(hour=int(h1), minute=int(m1))
    end = datetime.time(hour=int(h2), minute=int(m2))
    service, boolean_return = Service.objects.get_or_create(category=category,
                                  type=service_type,
                                  start_time=start,
                                  end_time=end,
                                  provider=provider,
                                  audience=audience,
                                  day=day,
                                  periodic=periodic,
                                  defaults = {'note': note or ''}
                                  )
    if report_status:
        return service, boolean_return
    return service


def insert_new_provider(**kwargs):
    # 1. Type Checking
    for key, value in kwargs.items():
        if value is not None and not isinstance(value, str):
            raise TypeError(f"Field '{key}' must be str, not {type(value).__name__}")

    # 2. Create the object
    # If 'name' isn't in kwargs, Django uses the model default ('No Provider')
    try:
        with transaction.atomic():
            provider = Provider.objects.create(**kwargs)
    except IntegrityError:
        return None

    # Note: .create() calls .save() automatically, so x.save() is redundant!
    return provider


def retrieve_provider(name, address=None):
    try:
        # If name is unique, this is all you need
        return Provider.objects.get(name=name)

    except Provider.DoesNotExist:
        return None

    except MultipleObjectsReturned:
        # This triggers if more than one provider has that name
        if address:
            # Narrow the search using the address
            try:
                return Provider.objects.get(name=name, address=address)
            except Provider.DoesNotExist:
                return None
        else:
            # You found many, but didn't provide an address to narrow it down
            raise LookupError(f"Multiple providers named '{name}' found. Address required to disambiguate.")

def insert_new_service_category(category):
    x = ServiceCategory.objects.get_or_create(category=category)
    return x[0]

def insert_new_service_type(type, category):
    if not isinstance(category, ServiceCategory):
        raise TypeError(f"Field '{type}' must be ServiceCategory.")

    x = ServiceType.objects.get_or_create(type=type, category=category)
    return x[0]

def retrieve_service_type(type):
    try:
        return ServiceType.objects.get(type=type)
    except ServiceType.DoesNotExist:
        return None

def retrieve_service_category(category):
    try:
        return ServiceCategory.objects.get(category=category)
    except ServiceCategory.DoesNotExist:
        return None

def insert_new_audience(audience):
    x = Audience.objects.get_or_create(audience=audience)
    return x[0]

def retrieve_audience(audience):
    try:
        return Audience.objects.get(audience=audience)
    except Audience.DoesNotExist:
        return None
