from server.models import Event


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