"""
Respository of helper functions for server app.
"""
import datetime
import logging
from warnings import deprecated

from django.utils import timezone
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError, transaction, models
import pytz

from server import event_info
from server.models import Event, Provider, ServiceCategory, ServiceType, \
    Audience, Service, Day, Update


def get_all_entries():
    pass


def get_service_type(event_query_set_obj):
    return event_query_set_obj.service_id.type


def get_service_category(event_query_set_obj):
    return event_query_set_obj.service_id.category


def get_provider_name(event_query_set_obj):
    return event_query_set_obj.service_id.provider.name


def get_service_location(event_query_set_obj):
    return event_query_set_obj.service_id.provider.address


def get_provider_phone_number(event_query_set_obj):
    return event_query_set_obj.service_id.provider.phone


def get_service_target_audience(event_query_set_obj):
    return event_query_set_obj.service_id.audience


def event_data_packer(entry, category_info):
    """
    Helper function for views.py, takes a models.Event object, returning
    JSON-friendly packaged data
    """
    service = entry.service_id

    # These .all() calls will now hit the PREFETCH cache
    # instead of the database, provided the View is set up right.
    service_types = service.type.all()

    return {
        'provider_name': service.provider.name,
        'address': service.provider.address,
        'phone': service.provider.phone,
        'email': service.provider.email,
        'service_category': list(
            {category_info.get(x.type) for x in service_types}),
        'service_type': [x.type for x in service_types],
        'audience': [x.audience for x in service.audience.all()],
        'start_time': entry.date.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': entry.end.strftime('%Y-%m-%d %H:%M:%S'),
        'notes': service.note,
    }


@deprecated("use event_data_packer() instead")
def pull_event_detail_view(event_id):
    """
    Helper function for former detail view in views.py, takes in the
    Event primary key id number (int), returns JSON-friendly data
    packet for specified event.
    """
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


def insert_new_service_event(service_type, day, start_time, end_time,
                             periodic, audience, provider, note=None,
                             report_status=False, category=None, ):
    if report_status:
        service, created = Service.objects.create_or_update_service(
            categories=category,
            types=service_type,
            day=day,
            start_time=start_time,
            end_time=end_time,
            periodic=periodic,
            audiences=audience,
            provider=provider,
            note=note,
            report_status=report_status)
        return service, created

    service = Service.objects.create_or_update_service(
        categories=category,
        types=service_type,
        day=day,
        start_time=start_time,
        end_time=end_time,
        periodic=periodic,
        audiences=audience,
        provider=provider,
        note=note,
        )
    return service


def insert_new_provider(**kwargs):
    report_status = kwargs.pop('report_status', False)
    for key, value in kwargs.items():
        if value is not None and not isinstance(value, str):
            raise TypeError(
                f"Field '{key}' must be str, not {type(value).__name__}")

    # 2. Extract unique lookup fields
    # We use .get() so we can handle defaults manually if they aren't in kwargs
    name_lookup = kwargs.get('name', None)
    address_lookup = kwargs.get('address', None)

    if name_lookup is None:
        raise ValueError("kwargs.name must me present")

    # 3. Get or Create
    # defaults: contains data used ONLY if creating a new record
    try:
        provider, created = Provider.objects.get_or_create(
            name=name_lookup,
            address=address_lookup,
            defaults=kwargs
        )
        if report_status:
            return provider, created
        return provider
    except IntegrityError:
        # This handles edge cases where a race condition might happen,
        # or if name/address lookup still fails.
        return Provider.objects.get(name=name_lookup,
                                    address=address_lookup)


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
            raise LookupError(
                f"Multiple providers named '{name}' found. Address required to disambiguate.")


def insert_new_service_category(category):
    x = ServiceCategory.objects.get_or_create(category=category)
    return x[0]


def insert_new_service_type(service_type, category):
    if not isinstance(category, ServiceCategory):
        raise TypeError(f"Field '{category}' must be ServiceCategory.")

    x = ServiceType.objects.get_or_create(type=service_type, category=category)
    return x[0]


def retrieve_service_type(service_type):
    try:
        return ServiceType.objects.get(type=service_type)
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


def retrieve_day(day_int):
    try:
        return Day.objects.get(id=day_int)
    except Day.DoesNotExist:
        return None


def purge_old_events():
    """
    Purges events from the Event table if their end_time and date has
    passed.
    """
    Event.objects.filter(end__lt=timezone.now()).delete()


# def update_event_table():
#     """
#     Refreshes the Service table and populates the Event calendar.
#     """
#     # 1. Update the Services first
#     # This ensures your Service table matches
#     # your data source (event_info)
#     sync_service_definitions()
#
#     # 2. Populate the Event Calendar
#     purge_old_events()
#
#     local_tz = pytz.timezone('US/Central')
#     today = datetime.date.today()
#     new_events = []
#
#     # Use prefetch_related to grab all 'days' at once (
#     # Performance Boost!)
#     services = Service.objects.prefetch_related('day').all()
#
#     for service in services:
#         # logging.error(f'entering')
#         # Get a set of weekday indices for this service
#         # (e.g., {0, 1, 2})
#         active_day_indices = set(
#             service.day.values_list('id', flat=True))
#
#         for offset in range(33):  # Look ahead 33 days
#             working_date = today + datetime.timedelta(days=offset)
#
#             if working_date.weekday() in active_day_indices:
#                 start_dt = local_tz.localize(
#                     datetime.datetime.combine(working_date,
#                                               service.start_time))
#                 end_dt = local_tz.localize(
#                     datetime.datetime.combine(working_date,
#                                               service.end_time))
#
#                 # Only add if it hasn't happened yet
#                 if end_dt > timezone.now():
#                     new_events.append(
#                         Event(service_id=service, date=start_dt,
#                               end=end_dt)
#                     )
#
#     # Use ignore_conflicts=True so we don't crash on existing events
#     Event.objects.bulk_create(new_events, ignore_conflicts=True)

# def update_event_table():
#     sync_service_definitions()
#     purge_old_events()
#
#     local_tz = pytz.timezone('US/Central')
#     today = datetime.date.today()
#
#     # FIX: Add chunk_size to the iterator
#     # 1000 is a safe balance for memory vs. performance on Render
#     services = Service.objects.prefetch_related('day').all().iterator(
#         chunk_size=1000)
#
#     batch_size = 500
#     new_events = []
#
#     for service in services:
#         # Get a set of weekday indices for this service
#         active_day_indices = set(
#             service.day.values_list('id', flat=True))
#
#         for offset in range(33):  # Look ahead 33 days
#             working_date = today + datetime.timedelta(days=offset)
#
#             if working_date.weekday() in active_day_indices:
#                 start_dt = local_tz.localize(
#                     datetime.datetime.combine(working_date,
#                                               service.start_time))
#                 end_dt = local_tz.localize(
#                     datetime.datetime.combine(working_date,
#                                               service.end_time))
#
#                 # Only add if it hasn't happened yet
#                 if end_dt > timezone.now():
#                     new_events.append(
#                         Event(service_id=service, date=start_dt,
#                               end=end_dt))
#
#                 # Bulk create in batches to keep memory usage flat
#                 if len(new_events) >= batch_size:
#                     Event.objects.bulk_create(new_events,
#                                               ignore_conflicts=True)
#                     new_events = []
#
#     if new_events:
#         Event.objects.bulk_create(new_events, ignore_conflicts=True)

from django.db.models import Max


def update_event_table(deep=False):
    # 1. Fast-sync definitions (see optimized function below)
    sync_service_definitions()

    # 2. Cleanup past events
    purge_old_events()


    # SHALLOW UPDATE
    # Normal update path; as events are removed from the table,
    # only new events are added. Will not adderss or fix events with
    # changes to corresponding Service-table entry or new Service-table
    # entries.
    if not deep:
        # 3. Get the "Max Date" for every service in a single query.
        # This identifies the "scheduling frontier" for each service.
        latest_event_map = {
            item['service_id']: item['latest'].date()
            for item in
            Event.objects.values('service_id').annotate(latest=Max('date'))
            if item['latest']
        }

        local_tz = pytz.timezone('US/Central')
        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=33)
        new_events = []
        batch_size = 500

        # 4. Process services. Use .iterator() to keep memory usage low on Render.
        services = Service.objects.prefetch_related('day').all().iterator(
            chunk_size=1000)

        for service in services:
            active_days = set(service.day.values_list('id', flat=True))

            # Determine where to start: either the day after the last event, or today.
            last_scheduled = latest_event_map.get(service.id,
                                                  today - datetime.timedelta(
                                                      days=1))
            start_date = max(today,
                             last_scheduled + datetime.timedelta(days=1))

            # Calculate the remaining window
            days_to_generate = (horizon - start_date).days + 1

            if days_to_generate <= 0:
                continue

            for offset in range(days_to_generate):
                working_date = start_date + datetime.timedelta(days=offset)

                if working_date.weekday() in active_days:
                    start_dt = local_tz.localize(
                        datetime.datetime.combine(working_date,
                                                  service.start_time))
                    end_dt = local_tz.localize(
                        datetime.datetime.combine(working_date,
                                                  service.end_time))

                    if end_dt > timezone.now():
                        new_events.append(
                            Event(service_id=service, date=start_dt,
                                  end=end_dt))

                    if len(new_events) >= batch_size:
                        Event.objects.bulk_create(new_events,
                                                  ignore_conflicts=True)
                        new_events = []

        if new_events:
            Event.objects.bulk_create(new_events, ignore_conflicts=True)

# def sync_service_definitions():
#     """
#     Reads from your event_info file and ensures the Service
#     records exist.
#     """
#     # Assuming your data source is here
#     current_service_data = Service.objects
#     for key, data in event_info.service_list.items():
#         logging.debug(
#             f'syncing data for {key}, data[\'provider\']: '
#             f'{data['provider']}')
#         # 1. Get the Provider (using your helper)
#         # logging.error(f'syncing for {key}, data: {data}')
#         provider = Provider.objects.get(name=data['provider'])
#
#         # 2. Create/Update the Service base object
#         # Note: We don't put ManyToMany fields in get_or_create
#
#         service, created = Service.objects.get_or_create(
#             provider=provider,
#             start_time=data['start_time'],
#             end_time=data['end_time'],
#             periodic=data.get('period', 0),
#             note=data.get('note', '')
#         )
#
#         # 3. Handle the Many-to-Many "Tagging"
#         # This is where we fix that TypeError you saw!
#
#         # Sync Audiences
#         # (Assuming your data has a list of audience names)
#         audience_names = data.get('audiences', data['audience'])
#         if not isinstance(audience_names, (list, models.QuerySet)):
#             audience_names = [audience_names]
#         audience_objs = Audience.objects.filter(
#             audience__in=audience_names)
#         service.audience.set(audience_objs)
#
#         # Sync Days
#         day_indices = data.get('day', [])  # e.g. [0, 1, 2]
#         if isinstance(day_indices, int):
#             day_indices = [day_indices]
#         day_objs = Day.objects.filter(id__in=day_indices)
#         service.day.set(day_objs)
#
#         # Sync Types/Categories
#         # This part handles the list indices logic that was crashing
#         type_names = list(data['service_type']) if isinstance(
#             data['service_type'], list) else [
#             data['service_type']]
#         type_objs = ServiceType.objects.filter(type__in=type_names)
#         service.type.set(type_objs)

# def sync_service_definitions():
#     # 1. Pre-fetch lookup data to avoid N+1 queries in the loop
#     providers = {p.name: p for p in Provider.objects.all()}
#     audiences = {a.audience: a for a in Audience.objects.all()}
#     # Note: If ServiceType names aren't unique across categories,
#     # this dictionary will only store the LAST one found.
#     types = {t.type: t for t in ServiceType.objects.all()}
#     days = {d.id: d for d in Day.objects.all()}
#
#     for key, data in event_info.service_list.items():
#         provider = providers.get(data['provider'])
#         if not provider:
#             continue
#
#             # FIX: 'note' must be in the lookup to satisfy the unique_together
#         # constraint defined in models.py
#         service, created = Service.objects.get_or_create(
#             provider=provider,
#             start_time=data['start_time'],
#             end_time=data['end_time'],
#             periodic=data.get('period', 0),
#             note=data.get('note', '')
#         )
#
#         # Process Audiences
#         aud_names = data.get('audiences', data.get('audience', []))
#         if isinstance(aud_names, str):
#             aud_names = [aud_names]
#         target_audiences = [audiences[n] for n in aud_names if
#                             n in audiences]
#         service.audience.set(target_audiences)
#
#         # Process Days
#         all_days = data.get('days', data.get('day', []))
#         if isinstance(all_days, int):
#             all_days = [all_days]
#         days_offered = [days[n] for n in all_days if n in days]
#         service.day.set(days_offered)
#
#         # FIX: Use 'service_type' key to match the data source
#         type_names = data.get('service_type', [])
#         if isinstance(type_names, str):
#             type_names = [type_names]
#
#         # FIX: Map strings to the pre-fetched objects
#         types_for_service = [types[n] for n in type_names if n in types]
#
#         # FIX: Pass the list of OBJECTS (types_for_service), not strings
#         service.type.set(types_for_service)

def sync_service_definitions():
    # 1. Bulk-fetch all metadata into memory dictionaries.
    # This reduces ~2,000 queries down to 4.
    providers = {p.name: p for p in Provider.objects.all()}
    audiences = {a.audience: a for a in Audience.objects.all()}
    types = {t.type: t for t in ServiceType.objects.all()}
    days = {d.id: d for d in Day.objects.all()}

    for key, data in event_info.service_list.items():
        provider = providers.get(data['provider'])
        if not provider:
            continue

        # Convert strings to time objects once
        start_t = data['start_time']
        if isinstance(start_t, str): start_t = datetime.time.fromisoformat(start_t)
        end_t = data['end_time']
        if isinstance(end_t, str): end_t = datetime.time.fromisoformat(end_t)

        # 2. Get or Create the service
        service, created = Service.objects.get_or_create(
            provider=provider,
            start_time=start_t,
            end_time=end_t,
            periodic=data.get('period', 0),
            note=data.get('note', '')
        )

        # 3. Only update Many-to-Many relationships if the service is NEW.
        # This prevents thousands of DELETE/INSERT operations on every hourly run.
        if created:
            # Sync Audiences
            aud_names = data.get('audiences', data.get('audience', []))
            if isinstance(aud_names, str): aud_names = [aud_names]
            service.audience.set([audiences[n] for n in aud_names if n in audiences])

            # Sync Days
            day_indices = data.get('day', [])
            if isinstance(day_indices, int): day_indices = [day_indices]
            service.day.set([days[n] for n in day_indices if n in days])

            # Sync Types
            type_names = data.get('service_type', [])
            if isinstance(type_names, str): type_names = [type_names]
            service.type.set([types[n] for n in type_names if n in types])

def get_all_categories_types():
    """
    Returns a dictionary of all service categories and related service
    types, schema {category: [type(s)]}.
    """
    data = {}
    # select_related('category') performs a SQL JOIN to get names in one hit
    # values_list avoids instantiating full Model objects
    queryset = ServiceType.objects.select_related(
        'category').values_list(
        'category__category', 'type'
    )

    for category_name, type_name in queryset:
        data.setdefault(category_name, []).append(type_name)
    return data

def get_all_audiences():
    """Returns an array of all audience types."""
    # .distinct() ensures the DB only sends unique values
    # flat=True returns a list of strings instead of a list of tuples
    return list(
        Audience.objects.values_list('audience', flat=True).distinct())

def get_all_provideers_json_format():
    data = {}
    providers = Provider.objects.all()

    for provider in providers:
        data.setdefault(provider.id, {})
        data[provider.id].setdefault('name', provider.name)
        data[provider.id].setdefault('phone', provider.phone)
        data[provider.id].setdefault('email', provider.email)

    return data